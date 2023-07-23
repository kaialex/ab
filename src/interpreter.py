from typing import List, Tuple
import re
from copy import deepcopy
import sys
import os
import argparse

class ABCommand:
  def __init__(self, command: str, line: int):
    self.line = line
    self.command = self.interpret(command, line)
    self.left = self.command["left"]
    self.right = self.command["right"]
    self.commandstring = command
  
  def interpret(self, input: str, line: int):
    index_key = ["left", "right"]
    command = {"left": {"content": "", "reserved": ""}, "right": {"content": "", "reserved": ""}}
    data = input.replace(" ","").replace("\n", "").split("=")
    if (len(data) != 2):
      self.raiseError("equal sign")
    
    for index, splitdata in enumerate(data):
      # 改行消す
      splitdata = splitdata.replace("\n", "")
      detail = self.getDetail(splitdata, index_key[index])
      if not detail["valid"]:
        self.raiseError("")
      
      command[index_key[index]]["content"] = detail["content"]
      command[index_key[index]]["reserved"] = detail["reserved"]
      
    return command
    
  def getDetail(self, command: str, leftorright: str):
    detail = {"valid": False, "content": "", "reserved": ""}
    
    if (command == ""):
      return {"valid": True, "content": "", "reserved": ""}
    
    
    if (leftorright == "left"):
      fullcheck =re.compile(r"(\((once|start|end)\))?(.*)")
    else:
      fullcheck = re.compile(r"(\((start|end|return)\))?(.*)")
    m = re.fullmatch(fullcheck, command)
    check = re.findall(r"(\(|\))", m.group(3))
    
    if (m is None):
      self.raiseError()
    if (len(check) > 0):
      self.raiseError("reserved word is over")
    detail["valid"] = True
    if (len(m.groups()) == 3):
      detail["reserved"] = m.group(2)
      detail["content"] = m.group(3)
    else:
      self.raiseError("reserved word is over")
    
    return detail
  
  def raiseError(self, reason = "unknown"):
    raise ValueError(f"Invalid command by {reason} at line: {self.line}")

class ABInterpreter:
  
  def __init__(self, filename: str, MAXLOOP: int = 100000):
    self.filename = filename
    self.commands: List[ABCommand] = self.readFile()
    self.MAXLOOP = MAXLOOP
  
  def readFile(self):
    commands: List[ABCommand] = []
    line = 0
    with open(f"{os.getcwd()}/code/{self.filename}.ab", 'r') as file:
      while command := file.readline():
        line += 1
        if (re.match(r"^#", command)):
          continue
        commands.append(ABCommand(command, line))
    return commands

  def run(self, input: str, detail: bool = False):
    print(f"start string: {input}")
    currentCommands = deepcopy(self.commands)
    currentString = input
    loop_num = 0 
    while loop_num < self.MAXLOOP:
      isFinished = False
      for command in currentCommands:
        isExecuted = False
        isValid, start, next_commands = self.checkLeft(currentString, command, currentCommands)
        if (not isValid):
          continue
        isExecuted = True
        currentString = currentString.replace(command.left["content"], "", 1)
        currentString, isFinished = self.addRight(currentString, command, start)
        if (detail):
          self.display(currentString, command)
        else:
          print(currentString)
        break
      currentCommands = next_commands
      if (isFinished or not isExecuted):
        break
      loop_num += 1
    
    print(f"output:{currentString}")
  
  def checkLeft(self, input: str, command, currentCommands: List[ABCommand]) -> Tuple[bool, int, List[ABCommand]]:
    leftcommand = command.left
    escaped_command = re.escape(leftcommand["content"])
    #startの時は最初が合ってるかチェック
    if (leftcommand["reserved"] == "start"):
      matchText = re.compile("^({})".format(escaped_command))
    #endの時は最後が合ってるかチェック
    elif (leftcommand["reserved"] == "end"):
      matchText = re.compile("({})$".format(escaped_command))
    #それ以外の時は一致する場所があるか最初からチェックし、1つ見つかればok
    else:
      matchText = re.compile("({})".format(escaped_command))
      
    match = re.search(matchText, input)
    if (match is None):
      return False, -1, currentCommands
    else:
      if (leftcommand["reserved"] == "once"):
        currentCommands.pop(currentCommands.index(command))
      return True, match.start(), currentCommands
      
  def addRight(self, input: str, command, startInput: int) -> Tuple[str, bool]:
    rightcommand = command.right
    if (rightcommand["reserved"] == "return"):
      return rightcommand["content"], True
    
    if (rightcommand["reserved"] == "start"):
      startInput = 0
    elif (rightcommand["reserved"] == "end"):
      startInput = len(input)
    
    if (input == ""):
      return rightcommand["content"], False
    listedInput = list(input)
    listedInput.insert(startInput, rightcommand["content"])
    return "".join(listedInput), False
    
      
  def display(self, currentString: str, command: ABCommand):
    print(f"line: {command.line}")
    print(f"command: {command.commandstring}")
    print(f"currentString: {currentString}")
    print("--------------------")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("filename", help="filename")
  parser.add_argument("input", help="input")
  parser.add_argument("-v", "--verbose", help="verbose", action="store_true")
  parser.add_argument("--maxloop", help="maxloop", type=int, default=1000)
  
  args = parser.parse_args()
  
  compiler = ABInterpreter(args.filename, args.maxloop)
  compiler.run(args.input, args.verbose)
    
    