# zzf-notifier
自住房公告自动通知，这个工具可以帮助申请自住房的小伙伴，第一时间去申请自住房，并且摇号结果出来后，能第一时间查看

# 如何开始

### 初始化sqlite数据库
```
$ sqlite3 data.db < schema.sql
```

### 创建Virtualenv环境
```
$ virtualenv venv
```

### 修改配置文件
将文件config_example.yml拷贝到config.yml中，然后修改smtp配置，并添加接收通知邮箱地址

### 初始化现有通告
```
$ ./venv/bin/python2.7 notify.py --init
```

### 添加crontab记录
```
0 * * * * cd $PROJECT_FOLDER/zzf-notifier && ./run.sh # run hourly
```

# TODO
  * 短信通知
  * 邮件/短信通知摇号结果
