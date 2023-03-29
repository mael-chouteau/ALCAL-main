#!/usr/bin/python3

#Author: Maël Chouteau

#Internal files import
import pdf
import secret
import Language.FR as verbose

#External libraries import
from bs4 import BeautifulSoup
import sys
import re
import datetime
import pytz
from icalendar import Calendar, Event
import os
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

#Firefox options to run in background (headless)
options = Options()
options.headless = True

#Driver initialization
driver = webdriver.Firefox( options=options)

cal = Calendar()
tz = pytz.timezone('Europe/Paris')
def main():
    print(verbose.CONNEXIONALCUIN)
    login_alcuin()
    precedent = ""
    #Move to the direcory of the main.py for the relative path
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    #Initialize possible parameters
    parser = argparse.ArgumentParser(description="Extracts ESAIP's calendar from Alcuin")
    parser.add_argument('days', type=int, help="Number of days to extract")
    parser.add_argument('promo', type=int, help="Promotion to extract 0=1A, 1=2A, 2=3A")
    parser.add_argument('-o', '--output', help="Output file")
    parser.add_argument('date', type=int, nargs='?', const=0, default=0, help="Number of days to add to today's date")
    
    args = parser.parse_args()

    #Convert the promo to the right format and put it in a variable
    promo = int(args.promo)

    #Remove the pdfs files if they exists from the promotion we want to extract
    os.system('rm -r '+secret.PATHTOPDF+secret.ANNEE[promo]+'/*.pdf')

    #Empty the ics file from the promotion we want to extract
    os.system('echo "" > '+secret.PATHTOPDF+secret.ANNEE[promo]+'/calendrier.ics')

    #If th user wants to output the file in a specific file we put it in a variable
    if args.output:
        sys.stdout = open(args.output, 'w+')
    
    #We first have to fo to this page to get the cookies    
    driver.get('https://esaip.alcuin.com/OpDotnet/commun/Login/aspxtoasp.aspx?url=/Eplug/Agenda/Agenda.asp?IdApplication=190&TypeAcces=Utilisateur&IdLien=5834&groupe=2483')
    print(verbose.EXTRACTIONDESJOURS)
    #For each day we want to extract
    for delta in range(args.days):
        #Taking into account the offset if there is one to set the strarting date
        datefrom = datetime.datetime.today() + datetime.timedelta(args.date)

        #Define the date that will be extracted and define the location of the date to have the right timezone
        date = tz.localize(datefrom + datetime.timedelta(days=delta))
        print(verbose.EXTRACTIONJOUR+format(date.strftime("%d/%m/%Y")))

        #Define the calendar variable that will hold the html page of the day extracted
        cal = retrieve_cal(date,promo)

        #For each event in the cal list (list created by beautifulsoup using the td tags in the html page)
        for course in cal:

            #Clean and extract the relevant data from the event to then use it
            cal_data = extract_cal_data(course)

            #We first check if there is an event, othewise there is no need to put nothing in the pdf and ics file
            if cal_data:
                #Add the event to the PDF
                pdf.main(date.strftime('%d/%m/%Y'),  cal_data[0], cal_data[2], cal_data[5], date, promo)

                #Add the event to the ics file
                build_event(date, cal_data[0], cal_data[1], cal_data[2], cal_data[4],promo)
                #Set the precedent event to the current one
    print(verbose.AGENDASYNCRONISE)

def login_alcuin():
    #Go to the login page
    driver.get("https://esaip.alcuin.com/OpDotNet/Noyau/Login.aspx")

    #Fill the login form
    driver.find_element(By.ID, "UcAuthentification1_UcLogin1_txtLogin").send_keys(secret.LOGIN)
    driver.find_element(By.ID, "UcAuthentification1_UcLogin1_txtPassword").send_keys(secret.PASS)

    #Click on the login button
    driver.find_element(By.ID, "UcAuthentification1_UcLogin1_btnEntrer").click()

    #Check if the login was successful
    try:
        assert "https://esaip.alcuin.com/OpDotNet/Noyau/Default.aspx?" == driver.current_url
        print(verbose.CONNEXIONALCUINOK)
    except:
        print(verbose.CONNEXIONALCUINNOK)

        #If the login failed we exit the program and close the driver
        driver.quit()
        sys.exit()

def retrieve_cal(d,promo):

    #Go to the calendar page of the promotion we want to extract at the date we want to extract
    driver.get("https://esaip.alcuin.com/EPlug/Agenda/Agenda.asp?NumDat="+d.strftime('%Y%m%d')+"&DebHor=08&FinHor=18&ValGra=60&NomCal="+secret.CALENDRIER[promo]+"&TypVis=Vis-Jrs.xsl")
    
    #Get the html code of the page using beautifulsoup and find all the events (td with the class "GEDcellsouscategorie")
    cal = BeautifulSoup(driver.page_source, "html.parser").find_all("td", {"class": "GEDcellsouscategorie", "valign": None})
    return(cal)

def extract_cal_data(course):

    #Extract the text from the event html code the course text is like the one below
    course = course.get_text() # Cours - Investigation numérique16H45-18H15TIAB AmalC110Investigation numériqueIRA5

    #Check if the is a course in the event (if the event is not empty). We check if the is an hour in the event
    if 'H' not in course:
        return None

    #Empty the list that will contain the hours of the event
    time = []

    #Extract all the hours of the event and put them in the list. The output is 2 list of 2 elements like the example below
    [time.append(re.split('H', i)) for i in re.findall('\d\dH\d\d', course)]   #[['08', '15'], ['09', '45']]

    #We split the text of the event to get the name of the event and the type of event
    course_name = re.split(';',re.split('- ', re.split('\d\dH\d\d', course)[0])[1])[0].replace('\xa0', '')
    course_type = re.split('- ', re.split('\d\dH\d\d', course)[0])[0].replace('\xa0', '')

    #If the name of the course correspond to something like "22-23 ING3 S6" we replace it my the course type wich is more helpful
    if re.findall('\d\d-\d\d',course_name):
        course_name = course_type

    #We get the name of the teacher wich is after the last hours and before the room
    course_teacher = re.split('([A-Z][a-zà-ÿ]{2,}(?=[A-Z]{2,}))', re.split('[A-Z]\d|Amphi', re.split('\d\dH\d\d', course)[2])[0])

    #If the teacher name is not empty we convert the list generated by re.split into a string
    #And we create the course description for the calendar
    length = len(course_teacher)-1
    if length == 0:
        course_teacher = course_teacher[0]
        course_description = course_type + "\x0a" + course_teacher
    else:

        #Otherwise we go through the list and we add the teacher name to the course description with a new line between each name
        i = 0
        course_description_tmp = ""
        while i < length:
            course_description_tmp = course_description_tmp + course_teacher[i]
            i += 1
            course_description_tmp = course_description_tmp + course_teacher[i] + "\x0a"
            i += 1
        #The course_teacher variable is used for the pdf filling, and the course_description is for the calendar description which includes the course type and all the teachers
        course_teacher = course_description_tmp + course_teacher[length]
        course_description = course_type + "\x0a" + course_teacher

    #Depending on the course type we set the color of the event (curently not supported by the ics format)
    if re.search('Examen', course_type):
        color_id = secret.COLORS[0]
    elif re.search('Cours', course_type):
        color_id = secret.COLORS[1]
    else:
        color_id = secret.COLORS[2]
    
    #We extract the part after the hours wich contains the room number
    salle = re.split('\d\dH\d\d', course)[-1]

    #There are just two amphi so no need to make a regex for it just look if it is present
    if re.search('Amphi A', course):
        salle = 'Amphi A'
    elif re.search('Amphi E', course):
        salle = 'Amphi E'

    #The rooms of building A and B just have two number so in order to avoid any wierd behaviour we limit it to two numbers
    elif re.search('[AB]\d{2,}', salle):
        salle = re.search('[AB]\d\d', salle).group(0)
        
    #For the other buildings we always have three numbers
    elif re.search('[CDEF]\d{3,}', salle):
        salle = re.search('[CDEF]\d{3,}', salle).group(0)
    else:
        salle = 'Non renseigné'
    return(time, salle, course_name, color_id, course_description, course_teacher)

#Fonction that adds all the infos about an event to the ics file in the ical format
def build_event(d, time, salle, course_name, course_description, promo):
    filename = secret.PATHTOPDF+secret.ANNEE[promo]+'/calendrier.ics'

    #Put the hours and minutes to the right format for the event
    debut = d.replace(hour=int(time[0][0]),minute=int(time[0][1]), second=0,)
    fin = d.replace(hour=int(time[1][0]), minute=int(time[1][1]), second=0)

    #Initialise the event variable that will hold the events infos
    event = Event()

    #Adding everything to the event
    event.add('summary', course_name)
    event.add('description', course_description)
    event.add('dtstart', debut)
    event.add('dtend', fin)
    event.add('location', salle)

    #Adding the event to the calendar
    cal.add_component(event)

    #Opening the ics file
    f = open(filename, 'wb') 

    #Append the event to the file thanks to the calendar variable converting the infos in the event variable to the right format
    f.write(cal.to_ical())
    f.close()
#Fonction that parse the xml output of this url : https://esaip.alcuin.com/OpDotNet/Eplug/Agenda/Application/ListeCal.aspx wich is the list of calendars, using beautifulsoup
def parse_calendars():
    #Get the page that is responsible for the list of calendars
    driver.get('https://esaip.alcuin.com/OpDotNet/Eplug/Agenda/Application/ListeCal.aspx')
    r = driver.page_source
    #Look for the arguments of the fonction call MajDivCal wich contains the list of calendars
    xml_cal = re.search("(?<=parent.MajDivCal\(')(.*\>)", r)
    soup = BeautifulSoup(xml_cal[0], 'lxml')
    #Get the list of calendars wich are on the td tag of the html code
    calendars = soup.find_all('td')
    #Create a list that will contain the names and ids of the calendars
    cal_list_id = []
    cal_list_name = []
    #Go through the list of calendars and add the name and id of each calendar to the list
    for cal in calendars:
        print (cal)
        if cal.get('style') in ('background:#FAFAFA;','background:#BEB4FF;'):
            cal_list_id.append(re.search("[A-Z]{3,}\d{3,}", cal.get('onclick'))[0])
            cal_list_name.append(cal.text.strip())
    return(cal_list_id,cal_list_name)

def usage():
    print(verbose.USAGE)
    
if __name__ == "__main__":
    main()
    driver.close()
