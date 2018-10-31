import json
import os
import subprocess


def valgrind_build_system_executor(make_env):
    result = build_system_executor(make_env, cc_version='--version', as_version='--version')

    with subprocess.Popen(['valgrind', '--version'], stdout=subprocess.PIPE) as p:
        stdout, _ = p.communicate(timeout=1)

        stdout_decoded = stdout.decode('utf-8').rstrip() if stdout else None
        if p.returncode == 0 and stdout_decoded:
            result['VALGRIND_version'] = stdout_decoded

    return result


def drmemory_build_system_executor(make_env):
    result = build_system_executor(make_env, cc_version='--version', as_version='--version')

    with subprocess.Popen([os.environ['DR_MEMORY'], '-version'], stdout=subprocess.PIPE) as p:
        stdout, _ = p.communicate(timeout=1)

        stdout_decoded = stdout.decode('utf-8').rstrip() if stdout else None
        if p.returncode == 0 and stdout_decoded:
            result['DRMEMORY_version'] = stdout_decoded

    return result


def qemu_build_system_executor(make_env):
    result = build_system_executor(make_env, cc_version='--version', as_version='--version')

    with subprocess.Popen(['qemu-x86_64', '-version'], stdout=subprocess.PIPE) as p:
        stdout, _ = p.communicate(timeout=1)

        stdout_decoded = stdout.decode('utf-8').rstrip() if stdout else None
        if p.returncode == 0 and stdout_decoded:
            result['QEMU_version'] = stdout_decoded

    return result


def boehmgc_build_system_executor(make_env):
    return build_system_executor(make_env, cc_version='--version', as_version='--version')

def diehard_build_system_executor(make_env):
    return build_system_executor(make_env, cc_version='--version', as_version='--version')

def execute_binary_analysis_tool(filepath, workdir, tool, exec_args, env=None, **kwargs):
    env_tool = [os.path.expandvars(value) if type(value) is str else value for value in tool]
    args = env_tool + [filepath, '--output=json'] + exec_args
    with subprocess.Popen(args, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env) as process:
        stdout, stderr = process.communicate(timeout=kwargs.get('timeout', 240))

        stdout_decoded = stdout.decode('utf-8') if stdout else None
        stderr_decoded = stderr.decode('utf-8') if stderr and process.returncode != 0 else None

        if stdout_decoded:
            try:
                return json.loads(stdout_decoded), stderr_decoded
            except ValueError:
                logger.exception('invalid benchmark result: \'%s\'', stdout_decoded)

        return None, stderr_decoded


def valgrind_executor(filepath, workdir, exec_args, **kwargs):
    return execute_binary_analysis_tool(filepath, workdir, ['valgrind', '--error-exitcode=1'], exec_args, **kwargs)


def callgrind_executor(filepath, workdir, exec_args, **kwargs):
    return execute_binary_analysis_tool(filepath, workdir, ['valgrind', '--error-exitcode=1', '--tool=callgrind'], exec_args, **kwargs)


def drmemory_executor(filepath, workdir, exec_args, **kwargs):
    return execute_binary_analysis_tool(filepath, workdir, ['${DR_MEMORY}', '-exit_code_if_errors', '1', '--'], exec_args, **kwargs)


def qemu_executor(filepath, workdir, exec_args, **kwargs):
    return execute_binary_analysis_tool(filepath, workdir, ['qemu-x86_64'], exec_args, **kwargs)


def boehmgc_executor(filepath, workdir, exec_args, **kwargs):
    env = os.environ.copy()
    env['LD_PRELOAD'] = env.get('GC_LIBRARY_PATH', '/usr/local/lib/libgc.so')
    return execute_binary_analysis_tool(filepath, workdir, [], exec_args, env=env, **kwargs)

def diehard_executor(filepath, workdir, exec_args, **kwargs):
    env = os.environ.copy()
    env['LD_PRELOAD'] = env.get('DIEHARD_PATH')
    return execute_binary_analysis_tool(filepath, workdir, [], exec_args, env=env, **kwargs)

valgrind_kwargs = {'build_system_func': valgrind_build_system_executor, 'exec_func': valgrind_executor}
callgrind_kwargs = {'build_system_func': valgrind_build_system_executor, 'exec_func': callgrind_executor}
drmemory_kwargs = {'build_system_func': drmemory_build_system_executor, 'exec_func': drmemory_executor}
qemu_kwargs = {'build_system_func': qemu_build_system_executor, 'exec_func': qemu_executor}
boehmgc_kwargs = {'build_system_func': boehmgc_build_system_executor, 'exec_func': boehmgc_executor}
diehard_kwargs = {'build_system_func': diehard_build_system_executor, 'exec_func': diehard_executor}

harness.add_runtime('valgrind-O3', {"CC": "${CLANG}", "AS": "${CLANG}", "CFLAGS": "-Wno-everything -O3", "PAPI": 0}, **valgrind_kwargs)
harness.add_runtime('callgrind-O3', {"CC": "${CLANG}", "AS": "${CLANG}", "CFLAGS": "-Wno-everything -O3", "PAPI": 0}, **callgrind_kwargs)
harness.add_runtime('drmemory-O3', {"CC": "${CLANG}", "AS": "${CLANG}", "CFLAGS": "-Wno-everything -O3"}, **drmemory_kwargs)
harness.add_runtime('qemu-O3', {"CC": "${CLANG}", "AS": "${CLANG}", "CFLAGS": "-Wno-everything -O3"}, **qemu_kwargs)
harness.add_runtime('boehmgc-O3', {"CC": "${CLANG}", "AS": "${CLANG}", "CFLAGS": "-Wno-everything -O3"}, **boehmgc_kwargs)
harness.add_runtime('diehard-O3', {"CC": "${CLANG}", "AS": "${CLANG}", "CFLAGS": "-Wno-everything -O3"}, **diehard_kwargs)
