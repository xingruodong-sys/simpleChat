from loguru import logger

# logger.add('Log/dbug.log', level='INFO')

logger.add(
    "Log/app_{time}.log",  # 文件名可以包含时间变量
    rotation="100 MB",  # 文件达到100MB时轮转
    retention="30 days",  # 保留30天的日志
    compression="zip",  # 压缩旧日志
    enqueue=True,  # 线程安全
    backtrace=True,  # 记录异常堆栈
    diagnose=True,  # 诊断模式
    level="INFO"  # 日志级别
)


trace = logger.trace
debug = logger.debug
info = logger.info
success = logger.success
error = logger.error
warning = logger.warning
critical = logger.critical
