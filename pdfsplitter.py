import io
import os
import time
import uuid

import PyPDF2
import cx_Oracle
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage

datadir = "path/to/reports"
reportdir = "path/to/final reports"


def split(path):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    stu_numbers = []
    stu_names = []
    indices = []
    dsn_tns = cx_Oracle.makedsn('connection', 'database ssid')
    db = cx_Oracle.connect(user='username', password='password', dsn=dsn_tns)
    cursor = db.cursor()  # assign db operation to cursor variable
    sql = '''UPDATE u_studentsuserfields u set u.ausd_hashkey = :hashid where u.studentsdcid = (SELECT s.dcid from
    students s where s.dcid = u.studentsdcid and s.student_number = :stu_numid) '''

    #begin the process extracting text data from reports
    anum = "Student ID:"  # begin text search param
    bnum = "Parent"  # end text search param
    aname = "Report for"
    bname = "School"
    count = 0
    # PDF Text Extraction
    with open(path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            indices.append(count)
            page_interpreter.process_page(page)
            count += 1
            text = fake_file_handle.getvalue()

            # Number Processing
            stu_num = text.split(anum)[-1].split(bnum)[0]
            stu_num = str(stu_num)
            stu_num = stu_num.strip()
            stu_num = stu_num.replace(" ", "")
            stu_numbers.append(stu_num)

            # Name Processing
            stu_name = text.split(aname)[-1].split(bname)[0]
            stu_name = str(stu_name)
            stu_name = stu_name.strip()
            stu_name = stu_name.replace("/x00", "")
            stu_name = stu_name.replace("\x00", "")
            stu_name = stu_name.replace("Student", "")
            stu_names.append(stu_name)

            print(stu_num + " " + stu_name + "'s report has been parsed")

    converter.close()
    fake_file_handle.close()

    # PDF Write Out
    pdf_file_obj = open(path, 'rb')  # open allows you to read the file
    pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)
    num_pages = pdf_reader.getNumPages()
    count2 = 0
    for page in range(pdf_reader.getNumPages()):
        while count2 < num_pages:  # The while loop will read each page
            pageobj = pdf_reader.getPage(count2)
            cur_stunum = stu_numbers[count2]
            pdf_writer = PyPDF2.PdfFileWriter()
            pdf_writer.addPage(pageobj)
            ausdhash = str(uuid.uuid4())
            # params = {'hashid': ausdhash, 'stu_numid': cur_stunum}
            # cursor.execute(sql, params)
            output_filename = '{}.pdf'.format(ausdhash)
            outdir = os.path.join(reportdir, output_filename)
            count2 += 1
            with open(outdir, "wb") as out:
                pdf_writer.write(out)
            print("generated " + cur_stunum + " " + output_filename)
    # db.commit()
    # cursor.close()
    # db.close()


def splitter():
    for file_name in os.listdir(datadir):
        if file_name.endswith(".pdf"):
            print("Preparing to Parse " + file_name)
            filepath = os.path.join(datadir, file_name)
            split(filepath)
    print("process complete")


splitter()
print(time.perf_counter() / 60)
