from functools import partial
import glob
import os
import subprocess

gcc_kwargs = {'build_system_func': partial(build_system_executor, cc_version='--version', as_version='--version')}

harness.add_runtime('gcc-O0', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O0"}, **gcc_kwargs)
harness.add_runtime('gcc-O1', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O1"}, **gcc_kwargs)
harness.add_runtime('gcc-O2', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O2"}, **gcc_kwargs)
harness.add_runtime('gcc-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3"}, **gcc_kwargs)
harness.add_runtime('gcc-Oz', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -Oz"}, **gcc_kwargs)
harness.add_runtime('gcc-lto-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -flto", "LDFLAGS": "-flto"}, **gcc_kwargs)
harness.add_runtime('gcc-stack-protector-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -fstack-protector"}, **gcc_kwargs)
harness.add_runtime('gcc-nostack-protector-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -fno-stack-protector"}, **gcc_kwargs)
harness.add_runtime('gcc-stack-protector-strong-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -fstack-protector-strong"}, **gcc_kwargs)
harness.add_runtime('gcc-stack-protector-all-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -fstack-protector-all"}, **gcc_kwargs)
harness.add_runtime('gcc-march-native-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -march=native"}, **gcc_kwargs)
harness.add_runtime('gcc-execstack-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -z execstack"}, **gcc_kwargs)
harness.add_runtime('gcc-nopie-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -no-pie"}, **gcc_kwargs)
harness.add_runtime('gcc-no-stack-protector-no-exec-stack-no-pie-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -fno-stack-protector -no-pie -z execstack"}, **gcc_kwargs)
harness.add_runtime('gcc-Ofast', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -Ofast"}, **gcc_kwargs)
harness.add_runtime('gcc-Os', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -Os"}, **gcc_kwargs)
harness.add_runtime('gcc-fno-strict-aliasing-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -fno-strict-aliasing"}, **gcc_kwargs)
harness.add_runtime('gcc-fno-strict-overflow-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -fno-strict-overflow"}, **gcc_kwargs)
harness.add_runtime('gcc-fno-delete-null-pointer-checks-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O3 -fno-delete-null-pointer-checks"}, **gcc_kwargs)
harness.add_runtime('gcc-gcov-O0', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O0 -fprofile-arcs -ftest-coverage"}, **gcc_kwargs)
harness.add_runtime('gcc-gprof-O0', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-std=gnu99 -O0 -pg"}, **gcc_kwargs)
harness.add_runtime('gcc-mpx-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": " -std=gnu99 -O3 -mmpx -fcheck-pointer-bounds -lmpxwrappers"}, **gcc_kwargs)
harness.add_runtime('introspection-mpx-O3', {"CC": "${GCC}", "AS": "as", "CFLAGS": " -std=gnu99 -O3 -mmpx -fcheck-pointer-bounds -lmpxwrappers -Wl,-E -include /safe-libc/libc.h /libc-mpx.o /mpx.o"}, **gcc_kwargs)  # NOQA: E501


# get line number coverage
def execute_gcov(filepath, workdir, exec_args, **kwargs):
    env = os.environ.copy()
    env['LC_ALL'] = 'C'
    with subprocess.Popen(['gcov', filepath, '-o', workdir, '-i'], cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env) as process:
        stdout, stderr = process.communicate(timeout=kwargs.get('timeout', 240))
        stdout_decoded = stdout.decode('utf-8') if stdout else None
    return stdout_decoded


def gcov_executor(filepath, workdir, exec_args, **kwargs):
    stdout, _, exit_code = default_executor(filepath, workdir, exec_args)  # execute file

    stderr_decoded = execute_gcov(filepath, workdir, exec_args, **kwargs)
    assert(filepath.endswith('_test'))
    benchmark_dir_name = filepath[:-5]
    for filename in glob.iglob(benchmark_dir_name + '/**/*.c', recursive=True):
        gcov_info = execute_gcov(filename, workdir, exec_args, **kwargs)
        if gcov_info is not None:
            stderr_decoded += gcov_info
    return stdout, stderr_decoded, exit_code


gcc_kwargs = {'build_system_func': partial(build_system_executor, cc_version='--version', as_version='--version'), 'exec_func': gcov_executor}

harness.add_runtime('gcc-gcov-line-numbers', {"CC": "${GCC}", "AS": "as", "CFLAGS": "-g -std=gnu99 -O0 --coverage", "LDFLAGS": "--coverage"}, **gcc_kwargs)
