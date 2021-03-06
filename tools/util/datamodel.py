from sqlalchemy import Column, ForeignKey, Boolean, Integer, BigInteger, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Harness(Base):
    __tablename__ = 'harness'
    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    benchmarks = relationship('Benchmark')
    executions = relationship('Execution')

    def __repr__(self):
        return '<Harness name="{}" benchmarks={}>'.format(self.name, self.benchmarks)


class Benchmark(Base):
    __tablename__ = 'benchmark'
    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    harness_id = Column(Integer, ForeignKey('harness.id'), nullable=False)

    harness = relationship("Harness", back_populates="benchmarks", lazy="joined")

    runs = relationship('Run')

    def __repr__(self):
        return '<Benchmark "{}">'.format(self.name)


class Configuration(Base):
    __tablename__ = 'configuration'
    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, unique=True, nullable=False)

    executions = relationship('Execution')

    def __repr__(self):
        return '<Configuration "{}">'.format(self.name)


class Compilation(Base):
    __tablename__ = 'compilation'
    id = Column(Integer, primary_key=True, nullable=False, index=True)
    cleaned = Column(Boolean, nullable=True)
    datetime = Column(DateTime, nullable=True)

    executions = relationship('Execution')
    build_system = relationship('CompilationBuildSystem', lazy="joined")
    make_env = relationship('CompilationMakeEnv', lazy="joined")

    def __repr__(self):
        return '<Compilation "{}">'.format(self.name)


class CompilationBuildSystem(Base):
    __tablename__ = 'compilation_build_system'
    compilation_id = Column(Integer, ForeignKey('compilation.id'), primary_key=True, nullable=False, index=True)
    key = Column(String,  primary_key=True, nullable=False)
    value = Column(String, nullable=False)

    compilation = relationship("Compilation", back_populates="build_system")

    def __repr__(self):
        return '<CompilationBuildSystem "{}" "{}"="{}">'.format(self.compilation_id, self.key, self.value)


class CompilationMakeEnv(Base):
    __tablename__ = 'compilation_make_env'
    compilation_id = Column(Integer, ForeignKey('compilation.id'), primary_key=True, nullable=False, index=True)
    key = Column(String,  primary_key=True, nullable=False)
    value = Column(String, nullable=False)

    compilation = relationship("Compilation", back_populates="make_env")

    def __repr__(self):
        return '<CompilationMakeEnv "{}" "{}"="{}">'.format(self.compilation_id, self.key, self.value)


class Execution(Base):
    __tablename__ = 'execution'
    id = Column(Integer, primary_key=True, nullable=False, index=True)
    harness_id = Column(Integer, ForeignKey('harness.id'), nullable=False)
    configuration_id = Column(Integer, ForeignKey('configuration.id'), nullable=False)
    compilation_id = Column(Integer, ForeignKey('compilation.id'), nullable=True)
    datetime = Column(DateTime, nullable=True)
    stderr = Column(String, nullable=True)
    stdout = Column(String, nullable=True)
    exit_code = Column(Integer, nullable=True)

    sys_platform = Column(String, nullable=True)
    sys_mem_avail = Column(BigInteger, nullable=True)
    sys_mem_free = Column(BigInteger, nullable=True)
    sys_mem_total = Column(BigInteger, nullable=True)
    sys_mem_used = Column(BigInteger, nullable=True)
    sys_cpu_logical = Column(Integer, nullable=True)
    sys_cpu_physical = Column(Integer, nullable=True)

    harness = relationship("Harness", back_populates="executions", lazy="subquery")
    configuration = relationship("Configuration", back_populates="executions")
    compilation = relationship("Compilation", back_populates="executions", lazy="subquery")

    runs = relationship('Run', lazy="subquery")
    sys_cpu = relationship('ExecutionSystemCpu', order_by="asc(ExecutionSystemCpu.idx)", lazy="joined")

    def __repr__(self):
        return '<Execution "{}" configuration={}>'.format(self.id, self.configuration)


class ExecutionSystemCpu(Base):
    __tablename__ = 'execution_system_cpu'
    execution_id = Column(Integer, ForeignKey('execution.id'), primary_key=True, nullable=False, index=True)
    idx = Column(Integer,  primary_key=True, nullable=False)
    percent = Column(Float, nullable=False)
    cur_clock = Column(Float, nullable=False)
    min_clock = Column(Float, nullable=False)
    max_clock = Column(Float, nullable=False)

    execution = relationship("Execution", back_populates="sys_cpu")

    def __repr__(self):
        return '<ExecutionSystemCpu "{}-{}" {}%>'.format(self.execution_id, self.idx, self.percent)


class Run(Base):
    __tablename__ = 'run'
    id = Column(Integer, primary_key=True, nullable=False, index=True)
    execution_id = Column(Integer, ForeignKey('execution.id'), nullable=False)
    benchmark_id = Column(Integer, ForeignKey('benchmark.id'), nullable=False)

    clock_resolution = Column(Float, nullable=True)
    clock_resolution_measured = Column(Float, nullable=True)
    clock_type = Column(String, nullable=True)
    disabled = Column(Boolean, nullable=False)
    iterations_per_run = Column(Integer, nullable=True)

    benchmark = relationship("Benchmark", back_populates="runs", lazy="joined")
    execution = relationship("Execution", back_populates="runs")

    datapoints = relationship('Datapoint', order_by="asc(Datapoint.idx)", lazy="subquery")

    def __repr__(self):
        return '<Run "{}">'.format(self.id)


class Datapoint(Base):
    __tablename__ = 'datapoint'
    idx = Column(Integer, primary_key=True, nullable=False)
    run_id = Column(Integer, ForeignKey('run.id'), primary_key=True, nullable=False, index=True)
    key = Column(String,  primary_key=True, nullable=False)
    value = Column(Float, nullable=False)

    run = relationship("Run", back_populates="datapoints")

    def __repr__(self):
        return '<Datapoint "{}-{}" "{}"="{}">'.format(self.idx, self.run_id, self.key, self.value)
