# 完成一个扫描代码中所有log的功能，项目文件为java，日志使用的是自定义log组件。这是一个例子：NMALogUtil.logI(TAG, "notifyLogStartClean done " + input)，其中NMALogUtil我自定义log的类，logI为输出函数，包含d,i,w,e等级的log，TAG一般定义在所在类或者父类的字符串成员变量。"notifyLogStartClean done"是输出的固定内容，input是需要打印出值的成员变量或者局部变量。
# 要求：
# 1. 扫描到log后，要记录TAG，所在文件，行数，内容
# 2. 可以通过筛选TAG，查看对应的log，保证查询效率
# 3. 提供一个模糊匹配的接口，实际的日志为02-28 11:06:15.140  3904  3904 I NeuRouteManagerImpl: [0.09.27.48.25.08.4a.42] notifyLogStartClean done 10 。 实际包括日期 时间 PID TID LEVEL TAG: [版本号] 输出内容 变量内容，我们需要匹配 TAG 输出内容。

# 后端实现：
# FASTApi
# 前端实现：
# 用VUE3，请酷炫一点
