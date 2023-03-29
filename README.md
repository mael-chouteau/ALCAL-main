# ALCAL
A little software that will scan a selected calandar in the alcuin's website of our ESAIP school and exports it to ICS file format

# Setup
Install python
```
sudo apt install python3
``` 
Download the geckodriver from https://github.com/mozilla/geckodriver/releases, make it executable and put it in /usr/local/bin/.

Clone the repository :
```
git clone https://github.com/mael-chouteau/ALCAL/
```
Or click on the "Clone or download" button

Then modify the secret.py.exmple by first renaming it to secret.py and modify the place holders by the right infos
```
LOGIN="login_alcuin"    <--- Your Alcuin ID
PASS="mdp_alcuin"     <--- Your Alcuin password
ANNEE = ["classe1","classe2","classe3"]     <--- Name of the differents years of your class IRA3 or GREA4 for exemple (It's for the folder's pdf's name)
CALENDRIER = ["PRJ15790","PRJ17091","PRJ16605"]     <--- ID of the calendar you want to extract. You can get it by analysing the get requests in yout browser. A version proposing the calendars is comming.
PATHTOPDF = "/home/user/Feuille-temps/"     <--- Absulute path to the destination folder for the PDFs and ics files generated
COLORS = ["ORANGE Category", "RED Category", "BLUE Category"]     <--- Colors for the Exams, courses, and other respectively.
```
# Installing the requirements

```
python3 -m pip install -r requirements.txt
```
# Utilisation

To launch the program to extract the next 120 days of the calendar of class 2:
```
py main.py 120 1
```

If you whant to offset the start of the extraction you just have to add another number at the end correspondig to the offset.
To start from 5 days in the future:

```
py main.py 120 1 5
```
# Tips

- To hide the firefox windows just change False to True at the line "options.headless".
- To change the language used in the logs just change FR to EN  at this lin "import Language.FR as verbose" or put EMPTY instead to remove logs.
