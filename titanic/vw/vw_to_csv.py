import csv
import re
i = 0
def clean(s):
  return " ".join(re.findall(r'\w+', s,flags = re.UNICODE | re.LOCALE)).lower()

def write_to(reader, outfile):
  i = 0
  for line in reader:
    i+= 1
    if i > 1:
      vw_line = ""
      if str(line[1]) == "1":
        vw_line += "1 '"
      else:
        vw_line += "-1 '"
      vw_line += str(line[0]) + " |f "
      vw_line += "passenger_class_"+str(line[2])+" "

      vw_line += "last_name_" + clean(line[3].split(",")[0]).replace(" ", "_") + " "
      vw_line += "title_" + clean(line[3].split(",")[1]).split()[0] + " "
      vw_line += "sex_" + clean(line[4]) + " "
      if len(str(line[5])) > 0:
        vw_line += "age:" + str(line[5]) + " "
      vw_line += "siblings_onboard:" + str(line[6]) + " "
      vw_line += "family_members_onboard:" + str(line[7]) + " "
      vw_line += "embarked_" + str(line[11]) + " "
      outfile.write(vw_line[:-1] + "\n")

with open("titanic/vw/titanic00", "r") as infile, open("titanic/vw/titanic00_s", "wb") as outfile:
  reader = csv.reader(infile)
  write_to(reader, outfile)

with open("titanic/vw/titanic01", "r") as infile, open("titanic/vw/titanic01_s", "wb") as outfile:
  reader = csv.reader(infile)
  write_to(reader, outfile)
