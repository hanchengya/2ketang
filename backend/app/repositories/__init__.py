# 数据访问层(repository): 封装 ORM 增删改查,把数据持久化从 service 业务逻辑里分离。
#
# 约定:
#   - 每个函数接收 db(Session) + 数据,返回保存条数
#   - 只管存取,不管停止信号/任务日志(那是 service 层的事)
#   - 单条记录保存失败用 log.exception 记录(带栈),不中断整批
