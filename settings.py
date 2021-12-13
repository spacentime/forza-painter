import json

settingsObj = {
  "minimum" : 3,
  "shapes": {
    "ellipsis": 16      
  }
}

class Settings:
    "This is a settings class"
    minimum = 4     

    def __init__(self):
      self.minimum = 3

    def echo(self):
      print('minimum is:')
      print(self.minimum)

def getSettings():    
  return Settings()

def printData(data):
#  print(json.dumps(settingsObj))
  print(data)
  return
  