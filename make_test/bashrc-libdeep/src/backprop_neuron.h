/*
 libdeep - a library for deep learning
 Copyright (C) 2013-2017  Bob Mottram <bob@freedombone.net>

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions
 are met:
 1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
 3. Neither the name of the University nor the names of its contributors
    may be used to endorse or promote products derived from this software
    without specific prior written permission.
 .
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE HOLDERS OR
 CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#ifndef DEEPLEARN_BACKPROP_NEURON_H
#define DEEPLEARN_BACKPROP_NEURON_H

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include <ctype.h>
#include <math.h>
#include <assert.h>
#include <omp.h>
#include "globals.h"
#include "deeplearn_random.h"

struct bp_n {
    int no_of_inputs;
    float * weights;
    float * last_weight_change;
    struct bp_n ** inputs;
    float min_weight,max_weight;
    float bias;
    float last_bias_change;
    float backprop_error;
    int excluded;

    float value;
    float value_reprojected;
    float desired_value;
};
typedef struct bp_n bp_neuron;

#define NEURONALLOC(n) n = (bp_neuron*)malloc(sizeof(bp_neuron));
#define NEURON_ARRAY_ALLOC(n, size) \
    n = (bp_neuron**)malloc((size)*sizeof(bp_neuron*));
#define NEURON_LAYERS_ALLOC(n, layers) \
    n = (bp_neuron***)malloc((layers)*sizeof(bp_neuron**));

int bp_neuron_init(bp_neuron * n,
                   int no_of_inputs,
                   unsigned int * random_seed);
void bp_neuron_add_connection(bp_neuron * dest,
                              int index, bp_neuron * source);
void bp_neuron_feedForward(bp_neuron * n,
                           float noise,
                           unsigned int dropout_percent,
                           unsigned int * random_seed);
void bp_neuron_backprop(bp_neuron * n);
void bp_neuron_learn(bp_neuron * n,
                     float learning_rate);
void bp_neuron_free(bp_neuron * n);
int bp_neuron_save(FILE * fp, bp_neuron * n);
int bp_neuron_load(FILE * fp, bp_neuron * n);
int bp_neuron_compare(bp_neuron * n1, bp_neuron * n2);
void bp_neuron_fix_weights(bp_neuron * n);
void bp_neuron_reproject(bp_neuron * n);

#endif
