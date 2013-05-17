import _winreg

CLASS_NAME = "RegistryEnv"

#
class RegistryEnv():

    #
    def __init__(self,appname = 'WesSoft',environment = 'Default'):
        self.__key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,"SOFTWARE\\%s\\%s" % (appname,environment))

    def __getitem__(self,value_name):
        #handle class variables prefixed by "__"
        if CLASS_NAME in value_name:
            return self.__dict__[value_name]
        else:
            try:
                value,type = _winreg.QueryValueEx(self.__key,value_name)
            except EnvironmentError:
                raise  KeyError("Key '%s' is not defined."%(value_name))
            return value

    def __setitem__(self,value_name, value):
        #handle class variables prefixed by "__"
        if CLASS_NAME in value_name:
            self.__dict__[value_name] = value
        else:
            _winreg.SetValueEx(self.__key, value_name,0, _winreg.REG_SZ, value)

    def __contains__(self,item):
            try:
                value,type = _winreg.QueryValueEx(self.__key,item)
                return True
            except EnvironmentError:
                return False

if __name__ == "__main__":
    env = RegistryEnv()

    env['temp'] = "assdff"

    print env['temp']

    for s in ["temp","temp2"]:
        if s in env:
            print "'%s' key exists" % (s)
        else:
            print "'%s' key does *not* exists" % (s)
