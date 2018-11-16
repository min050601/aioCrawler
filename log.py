import logging




class SpiderLog():
    def __init__(self,level_str='DEBUG',format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',datefmt='%a, %d %b %Y %H:%M:%S',filename=None,filemode='w',):
        assert level_str in['DEBUG','INFO','WARNING','ERROR','CRITICAL'],'the log level contains(DEBUG,INFO,WARNING,ERROR,CRITICAL),has not %s'%level_str
        self.format=format
        self.datefmt=datefmt
        self.filename=filename
        self.filemode=filemode
        self.logging=logging
        self.level=getattr(self.logging,level_str)
        self.logging.basicConfig(level=self.level,
                            format=self.format,
                            datefmt=self.datefmt,
                            filename=self.filename,
                            filemode=self.filemode)




def messages(mess):
   message= '\n'+'\n'.join(['request(status_code:%s)count:%s'%(key,value) for key,value in mess.items()])
   return message


