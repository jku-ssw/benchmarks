/*
 * imgd.c
 *
 * Image comparison/diff example using libsrt
 *
 * Copyright (c) 2015-2016, F. Aragon. All rights reserved. Released under
 * the BSD 3-Clause License (see the doc/LICENSE file included).
 *
 * Observations:
 * - In order to have PNG and JPEG support: make imgc HAS_JPG=1 HAS_PNG=1
 */

#include "imgtools.h"

static int exit_with_error(const char **argv, const char *msg,
			   const int exit_code);

int main(int argc, const char **argv)
{
	size_t in_size = 0;
	struct RGB_Info ri1, ri2;
	ss_t *iobuf = NULL, *rgb1_buf = NULL, *rgb2_buf = NULL, *rgb3_buf = NULL;
	int exit_code = 2;
	FILE *fin = NULL, *fout = NULL;
	const char *exit_msg = "not enough parameters";
	int filter = F_None;
	#define IMGC_XTEST(test, m, c)	\
		if (test) { exit_msg = m; exit_code = c; break; }
	for (;;) {
		if (argc < 2)
			break;
		sbool_t ro = argc < 3 ? S_TRUE : S_FALSE;
		enum ImgTypes t_in1 = file_type(argv[1]),
			      t_in2 = file_type(argv[2]),
			      t_out = argc < 4 ? IMG_none : file_type(argv[3]);
		IMGC_XTEST(t_in1 == IMG_error || t_in2 == IMG_error ||
			   t_out == IMG_error, "invalid parameters",
			   t_in1 == IMG_error || t_in2 == IMG_error ? 3 : 4);

		fin = fopen(argv[1], "rb");
		iobuf = ss_dup_read(fin, MAX_FILE_SIZE);
		in_size = ss_size(iobuf);
		IMGC_XTEST(!in_size, "input #1 read error", 5);

		size_t rgb1_bytes = any2rgb(&rgb1_buf, &ri1, iobuf, t_in1);
		IMGC_XTEST(!rgb1_bytes, "can not process input file #1", 6);

		fclose(fin);
		fin = fopen(argv[2], "rb");
		ss_read(&iobuf, fin, MAX_FILE_SIZE);
		in_size = ss_size(iobuf);
		IMGC_XTEST(!in_size, "input #2 read error", 7);

		size_t rgb2_bytes = any2rgb(&rgb2_buf, &ri2, iobuf, t_in2);
		IMGC_XTEST(!rgb2_bytes, "can not process input file #2", 8);

		IMGC_XTEST(ss_size(rgb1_buf) != ss_size(rgb2_buf),
			   "can not process input file #2", 9);

		exit_code = rgbdiff(&rgb3_buf, rgb1_buf, &ri1, rgb2_buf, &ri2) ? 1 : 0;

		if (exit_code == 1)
			fprintf(stderr, "Image files %s and %s differ\n", argv[1], argv[2]);

		if (t_out != IMG_none) {
			size_t enc_bytes = rgb2type(&iobuf, t_out, rgb3_buf, &ri1, F_None);
			IMGC_XTEST(!enc_bytes, "output file encoding error", 10);

			fout = fopen(argv[3], "wb+");
			ssize_t written = ss_write(fout, iobuf, 0, ss_size(iobuf));

			IMGC_XTEST(!ro && (written < 0 ||
				   (size_t)written != ss_size(iobuf)),
				   "write error", 11);
		}
		break;
	}
	ss_free(&iobuf, &rgb1_buf, &rgb2_buf, &rgb3_buf);
	if (fin)
		fclose(fin);
	if (fout)
		fclose(fout);
	return exit_code > 1 ? exit_with_error(argv, exit_msg, exit_code) : 0;
}

static int exit_with_error(const char **argv, const char *msg,
			   const int exit_code)
{
	const char *v0 = argv[0];
	fprintf(stderr, "Error [%i]: %s\nSyntax: %s in1." FMT_IMGS_IN " in2."
		FMT_IMGS_IN " [out." FMT_IMGS_OUT "]\nExit code 0: matching "
		"images, 1: not matching.\nExamples:\n"
		IF_PNG("\tDiff: %s input1.png input2.png output.ppm\n")
		IF_JPG("\tDiff: %s input1.jpg input2.jpg output.tga\n")
		"\tDiff: %s input.ppm output.tga\n",
		exit_code, msg, v0, IF_PNG(v0 MY_COMMA) IF_JPG(v0 MY_COMMA) v0);
	return exit_code;
}

