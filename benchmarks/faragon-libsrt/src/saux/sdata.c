/*
 * sdata.c
 *
 * Dynamic size data handling. Helper functions, not part of the API.
 *
 * Copyright (c) 2015-2016, F. Aragon. All rights reserved. Released under
 * the BSD 3-Clause License (see the doc/LICENSE file included).
 */ 

#include "sdata.h"
#include "scommon.h"

/*
 * Allocation heuristic configuration
 *
 * SD_GROW_PCT (e.g. 25%): if possible, allocate at least 25% the current
 * allocated memory.
 * SD_GROW_MAX_INC: maximum amount of over-incremented elements.
 */

#ifdef S_MINIMAL
#define SD_GROW_PCT	10
#else
#define SD_GROW_PCT	25
#endif
#define SD_GROW_MAX_INC	1000000

static sd_t sd_void0 = EMPTY_SDataFull;
sd_t *sd_void = &sd_void0;

/*
 * Allocation
 */

sd_t *sd_alloc(const uint8_t header_size, const size_t elem_size,
	       const size_t initial_reserve, const sbool_t dyn_st,
	       const size_t extra_tail_bytes)
{
	size_t alloc_size = sd_alloc_size_raw(header_size, elem_size,
					      initial_reserve, dyn_st);
	sd_t *d = (sd_t *)s_malloc(alloc_size + extra_tail_bytes);
	if (d) {
		sd_reset(d, header_size, elem_size, initial_reserve, S_FALSE,
			 dyn_st);
		S_PROFILE_ALLOC_CALL;
	} else {
		S_ERROR("not enough memory");
		d = sd_void;
	}
	return d;
}

sd_t *sd_alloc_into_ext_buf(void *buffer, const size_t max_size,
			    const uint8_t header_size, const size_t elem_size,
			    const sbool_t dyn_st)
{
	RETURN_IF(!buffer || !max_size, NULL); /* not enough memory */
	sd_t *d = (sd_t *)buffer;
	sd_reset(d, header_size, elem_size, max_size, S_TRUE, dyn_st);
	return d;
}

void sd_free(sd_t **d)
{
	if (d && *d) {
		/*
		 * Request for freeing external buffers are ignored
		 */
		S_ASSERT(!(*d)->f.ext_buffer);
		if (!(*d)->f.ext_buffer)
			s_free(*d);
		*d = NULL;
	}
}

void sd_free_va(sd_t **first, va_list ap)
{
	sd_t **next = first;
	while (!s_varg_tail_ptr_tag(next)) { /* last element tag */
		if (next) {
			sd_free((sd_t **)next);
			*next = NULL;
		}
		next = (sd_t **)va_arg(ap, sd_t **);
	}
}

void sd_reset(sd_t *d, const uint8_t header_size, const size_t elem_size,
	      const size_t max_size, const sbool_t ext_buf,
	      const sbool_t dyn_st)
{
	if (d) {
		d->f.ext_buffer = ext_buf;
		sd_reset_alloc_errors(d);
		d->f.flag1 = d->f.flag2 = d->f.flag3 = d->f.flag4 = 0;
		d->f.st_mode = !dyn_st ?	  SData_Full :
				max_size <= 255 ? SData_DynSmall :
						  SData_DynFull;
		if (sdx_full_st(d)) {
			d->header_size = header_size;
			d->elem_size = elem_size;
			d->sub_type = 0;
		} else {
			((struct SDataSmall *)d)->aux = 0;
		}
		sdx_set_size(d, 0);
		sdx_set_max_size(d, max_size);
	}
}

/* Acknowledgements: similar to git's strbuf_grow */
size_t sd_grow(sd_t **d, const size_t extra_size, const size_t extra_tail_bytes)
{
	ASSERT_RETURN_IF(!d, 0);
	size_t size = sd_size(*d);
	ASSERT_RETURN_IF(s_size_t_overflow(size, extra_size), 0);
	size_t new_size = sd_reserve(d, size + extra_size, extra_tail_bytes);
	return new_size >= (size + extra_size) ? (new_size - size) : 0;
}

S_INLINE size_t sd_reserve_aux(sd_t **d, size_t max_size,
			       uint8_t full_header_size,
			       const size_t extra_tail_bytes)
{
	RETURN_IF(!d || !*d || (*d)->f.st_mode == SData_VoidData, 0);
	const size_t curr_max_size = sdx_max_size(*d);
	if (curr_max_size < max_size) {
		if ((*d)->f.ext_buffer) {
			S_ERROR("out of memory on fixed-size "
				"allocated space");
			sd_set_alloc_errors(*d);
			return curr_max_size;
		}
#ifdef SD_ENABLE_HEURISTIC_GROWTH
		size_t inc = s_size_t_pct(max_size, SD_GROW_PCT);
		inc = S_MIN(inc, SD_GROW_MAX_INC);
		if (!s_size_t_overflow(max_size, inc))
			max_size += inc;
#endif
		sbool_t is_dyn = sdx_dyn_st(*d);
		int chg = sdx_chk_st_change(*d, max_size);
		uint8_t curr_hdr_size = sdx_header_size(*d);
		uint8_t next_hdr_size = chg > 0 ?
					full_header_size :
					curr_hdr_size;
		size_t elem_size = sdx_elem_size(*d);
		size_t as = sd_alloc_size_raw(full_header_size,
					      elem_size, max_size, is_dyn);
		sd_t *d_next = (sd_t *)s_realloc(*d, as + extra_tail_bytes);
		if (!d_next) {
			S_ERROR("sd_reserve: not enough memory");
			sd_set_alloc_errors(*d);
			return curr_max_size;
		}
		*d = d_next;
		S_PROFILE_ALLOC_CALL;
		if (chg > 0) { /* Change from small to full container*/
			size_t size = ((struct SDataSmall *)d_next)->size;
			char *p = (char *)d_next;
			memmove(p + next_hdr_size, p + curr_hdr_size, size);
			d_next->f.st_mode = SData_DynFull;
			d_next->header_size = full_header_size;
			d_next->sub_type = 0;
			d_next->elem_size = 1;
			d_next->size = size;
		}
		sdx_set_max_size(*d, max_size);
	}
	return sdx_max_size(*d);
}

size_t sd_reserve(sd_t **d, size_t max_size, const size_t extra_tail_bytes)
{
	RETURN_IF(!d || !*d, 0);
	return sd_reserve_aux(d, max_size, (*d)->header_size, extra_tail_bytes);
}

size_t sdx_reserve(sd_t **d, size_t max_size, uint8_t full_header_size,
		   const size_t extra_tail_bytes)
{
	RETURN_IF(!d || !*d, 0);
	return sd_reserve_aux(d, max_size, full_header_size, extra_tail_bytes);
}

sd_t *sd_shrink(sd_t **d, const size_t extra_tail_bytes)
{
	ASSERT_RETURN_IF(!d || !(*d), sd_void); /* BEHAVIOR */
	RETURN_IF((*d)->f.ext_buffer, *d); /* non-shrinkable */
	RETURN_IF(!sdx_full_st(*d), *d); /* BEHAVIOR: shrink only full st */
	size_t max_size = sd_max_size(*d);
	size_t new_max_size = (*d)->size;
	if (new_max_size < max_size) {
		size_t as = sd_alloc_size_raw((*d)->header_size,
					      (*d)->elem_size, new_max_size,
					      S_FALSE);
		sd_t *d_next = (sd_t *)s_realloc(*d, as + extra_tail_bytes);
		if (d_next) {
			*d = d_next;
			(*d)->max_size = new_max_size;
		} else {
			S_ERROR("sd_shrink: warning realloc error");
		}
	}
	return *d;
}

