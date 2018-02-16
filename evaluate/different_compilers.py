#!/usr/bin/env python3

import argparse
import os
import re
import signal
import sqlite3
import subprocess
import time

DATABASE_FILE = "evaluation.db"


def parse_exec_output(stdout):
    return float(re.findall(r"execution time: ([0-9\.]+)ms", str(stdout))[0])


def timeout_handling(process):
    print("    TIMEOUT")
    process.send_signal(signal.SIGKILL)
    process.terminate()
    process.wait()
    return None

def run_benchmark(workdir, file):
    time.sleep(1)
    process = subprocess.Popen(["./{}".format(file)], cwd=workdir, stdout=subprocess.PIPE)
    stdout, _ = process.communicate(timeout=60)

    if process.returncode != 0:
        return None

    return parse_exec_output(stdout)


def run_lli_benchmark(workdir, file):
    process_bc = subprocess.Popen(["extract-bc", file], cwd=workdir)
    process_bc.wait(timeout=10)

    process = subprocess.Popen(["lli",  "{}.bc".format(file)], cwd=workdir, stdout=subprocess.PIPE)
    stdout, _ = process.communicate(timeout=60)

    if process.returncode != 0:
        return None

    return parse_exec_output(stdout)


SULONG_EXEC_DIR = '/home/thomas/JKU/java-llvm-ir-builder-dev/sulong'
SULONG_TIMEOUT = 20*10
SULONG_1000_TIMEOUT = (100+10)*10

def run_sulong_benchmark(workdir, file):
    process_bc = subprocess.Popen(["extract-bc", file], cwd=workdir)
    process_bc.wait(timeout=10)

    time.sleep(1)
    process = subprocess.Popen(["mx", "-p", SULONG_EXEC_DIR, "--timeout={}".format(SULONG_TIMEOUT), "lli",  "{}.bc".format(file)], cwd=workdir, stdout=subprocess.PIPE)
    try:
        stdout, _ = process.communicate(timeout=SULONG_TIMEOUT+5)
    except subprocess.TimeoutExpired:
        return timeout_handling(process)

    if process.returncode != 0:
        return None

    return parse_exec_output(stdout)


def run_sulong_jdk_1000_benchmark(workdir, file):
    print("    ...run test with full compilation")

    time.sleep(1)
    process = subprocess.Popen(["mx", "-p", SULONG_EXEC_DIR, "--timeout={}".format(SULONG_1000_TIMEOUT), "--jdk", "jvmci", "--dynamicimports=/compiler",
                                "lli",  "{}.bc".format(file), "-w=101",
                                "-Dgraal.TruffleCompilationThreshold=10"], cwd=workdir, stdout=subprocess.PIPE)
    try:
        stdout, _ = process.communicate(timeout=SULONG_1000_TIMEOUT+5)
    except subprocess.TimeoutExpired:
        print("    TIMEOUT")
        process.terminate()
        return None

    if process.returncode != 0:
        return None

    fast_exec_time = parse_exec_output(stdout)
    print("    full evalulation finished: {}s".format(fast_exec_time))

    db.add_entry("{}-100".format(compiler), testcase, fast_exec_time)


def run_sulong_jdk_benchmark(workdir, file):
    process_bc = subprocess.Popen(["extract-bc", file], cwd=workdir)
    process_bc.wait(timeout=10)

    time.sleep(1)
    process = subprocess.Popen(["mx", "-p", SULONG_EXEC_DIR, "--timeout={}".format(SULONG_TIMEOUT), "--jdk", "jvmci", "--dynamicimports=/compiler", "lli",  "{}.bc".format(file)], cwd=workdir, stdout=subprocess.PIPE)
    try:
        stdout, _ = process.communicate(timeout=SULONG_TIMEOUT+5)
    except subprocess.TimeoutExpired:
        print("    TIMEOUT")
        process.terminate()
        return None

    if process.returncode != 0:
        return None

    normal_exec_time = parse_exec_output(stdout)

    try:
        run_sulong_jdk_1000_benchmark(workdir, file)
    except:
        pass

    return normal_exec_time


COMPILERS = {
    "gcc" : {"make": {"CC": "gcc", "AS": "as", "CFLAGS": "", "LDFLAGS": ""}},
    "clang" : {"make": {"CC": "clang", "AS": "clang", "CFLAGS": "", "LDFLAGS": ""}},
    "lli" : {"make": {"CC": "wllvm", "AS": "wllvm", "CFLAGS": "", "LDFLAGS": ""}, "exec": run_lli_benchmark},
    #"sulong" : {"make": {"CC": "wllvm", "AS": "wllvm", "CFLAGS": "", "LDFLAGS": ""}, "exec": run_sulong_benchmark},
    #"sulong-jdk" : {"make": {"CC": "wllvm", "AS": "wllvm", "CFLAGS": "", "LDFLAGS": ""}, "exec": run_sulong_jdk_benchmark},
}

class EvaluationDb(object):
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.conn.execute("PRAGMA journal_mode=WAL")

        self.create_tables()

        self.c = self.conn.cursor()

    def create_tables(self):
        query = """CREATE TABLE IF NOT EXISTS`EVALUATION_RAW` (
            `NAME`	TEXT NOT NULL,
            `TESTCASE`	INTEGER NOT NULL,
            `EXECUTION_TIME_MS`	REAL NOT NULL,
            PRIMARY KEY(`NAME`,`TESTCASE`)
        );"""
        self.conn.execute(query)

    def add_entry(self, name, testcase, execution_time):
        query = """INSERT INTO EVALUATION_RAW (
            NAME,
            TESTCASE,
            EXECUTION_TIME_MS
            )

            VALUES(?, ?, ?);

        """

        tupel = (
            name,
            testcase,
            execution_time
        )

        try:
            self.c.execute(query, tupel)
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Execute tests for all given compilers with their parameters')
    parser.add_argument('testdir', type=str, help='directory where the tests and the Makefile is contained', action='store')
    #parser.add_argument('testcases', type=str, help='list of testcases to execute', action='store')

    args = parser.parse_args()

    if not os.path.isdir(args.testdir):
        print('"{0}" is not an existing directory!'.format(os.path.realpath(args.testdir)))
        exit(1)

    db = EvaluationDb()

    for compiler in COMPILERS:
        params = COMPILERS[compiler].get('make', {})

        # clean directory
        process = subprocess.Popen(['make', 'clean'], cwd=args.testdir, stdout=subprocess.DEVNULL)
        process.communicate()

        make_params = []
        for key  in params:
            make_params.append("{}={}".format(key, params[key]))

        # build all tests
        process = subprocess.Popen(['make'] + make_params, cwd=args.testdir)
        process.communicate()

        # execute all tests
        for testcase in sorted(os.listdir(args.testdir)):
            if not testcase.endswith("_test"):
                continue

            print(" * Run Benchmark for: {}".format(testcase))
            try:
                bench_func = COMPILERS[compiler].get('exec', run_benchmark)
                exec_time = bench_func(args.testdir, testcase)
                if exec_time is not None:
                    print("   Finished: {}s".format(exec_time))
                    db.add_entry(compiler, testcase, exec_time)
                else:
                    print("   EXIT CODE != 0")
            except RuntimeError:
                print("   FAILED!")