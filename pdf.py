#!/usr/bin/python3

#Author: Maël Chouteau

#Internal files import
import secret

#External libraries import
from PyPDF2 import PdfWriter, PdfReader, PdfMerger
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import mm
from reportlab.lib.colors import black
from datetime import datetime  


def main(date, horaire, cours, prof, dateweek, promo):

    #Put the hours and minutes into separated varibles to make the code simpler
    H1 = horaire[0][0]
    H2 = horaire[1][0]
    M1 = horaire[0][1]
    M2 = horaire[1][1]

    #Calculate the time difference between the start and the end of the event to put it in the right plave on the PDF
    tdelta = datetime.strptime(H2+M2, '%H%M') - datetime.strptime(H1+M1, '%H%M')

    #Convert the seconds to hours and then convert the remaining seconds to minutes
    HD, reste = divmod(tdelta.seconds, 3600)
    MD = divmod(reste, 60)

    #Define the variable that will hold the canvas infos to then create an new pdf with just the infos and fuse it to the template PDF
    packet = io.BytesIO()

    #Define the canvas to be exactly A4 size in landscape
    can = canvas.Canvas(packet, pagesize=(297*mm, 210*mm))

    #Write each infos to the right place in the PDF
    can.drawString(24 * mm, 178 * mm, date) #The date on the top left
    can.drawString(108 * mm, 167 * mm, str(HD) + "H" + str(MD[0])) #The duration of the event in the middle
    can.drawString(188 * mm, 181 * mm, H1 + "H" + M1)   #Start time
    can.drawString(182 * mm, 177 * mm, H2 + "H" + M2)   #End time
    can.setFont("Helvetica-Bold", 8)    #Set the font in bold for the course name
    can.drawString(32 * mm, 167 * mm, cours) #Course name

    # In case of multiple teachers we split them and then add as new line
    #Define the text box that will hold the teachers names
    textobject = can.beginText(236 * mm, 178 * mm)
    textobject.setFont("Helvetica", 8)
    
    #Split each teachers using the code used to return line in the ics file
    prof = prof.split('\x0a')
    for line in prof:
        textobject.textLine(line)
    can.drawText(textobject)

    #Turn the end hour to a number to check if the event is in the morning or the evening to check the right box
    H2 = int(H2)
    can.setFillColor(black)
    if H2 < 13:
        can.rect(81*mm, 178*mm, 2*mm, 1.75*mm, fill=1)
    else:
        can.rect(104*mm, 178*mm, 2*mm, 1.75*mm, fill=1)

    can.save()

    #move to the beginning of the StringIO buffer
    packet.seek(0)

    #Get the week number to name the pdf
    week_num = dateweek.isocalendar().week
    destfilename=secret.PATHTOPDF+secret.ANNEE[promo]
    filename = destfilename+'/%s.pdf' % week_num
    reference_pdf = PdfReader(open('./PDFs-presence/FichePrésence-'+secret.ANNEE[promo]+'.pdf', "rb"))
    output = PdfWriter()
    merger = PdfMerger()

    #Create a new PDF with Reportlab
    new_pdf = PdfReader(packet)

    #Check if the pdf for the current week already exist or if we need to create one
    if os.path.isfile(filename):
        #Open the existing pdf
        existing_pdf = PdfReader(open(filename, "rb"))
        
        #Add the empty pdf generated before to the reference pdf and then merge them to make it look like we wrote on the referance pdf
        page = reference_pdf.pages[0]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

        #Write "output" to a real temporary file
        outputstream = open(destfilename+'/temp.pdf', 'wb')
        output.write(outputstream)
        outputstream.close()

        #Add the temporary file to the pdf holding every pages of the events of the week
        merger.append(existing_pdf)
        merger.append(destfilename+'/temp.pdf')
        merger.write(filename)

    else:

        #Add the empty pdf generated before to the reference pdf and then merge them to make it look like we wrote on the referance pdf
        page = reference_pdf.pages[0]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

        #Write "output" directly to the pdf of the week because it's the first event on the pdf
        outputstream = open(filename, 'wb')
        output.write(outputstream)
        outputstream.close()
    
