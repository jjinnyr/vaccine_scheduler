'''
This is a vaccine scheduling applicadtion with a database hosted on Microsoft Azure,
and it supports interaction with users through the terminal/command-line interface.
'''

### It is assumed that three types of vaccines are provided: Moderna, Pfizer, and Johnson.
### Johnson & Johnson vaccine is registered as "Johnson."
### No other names for Johnson & Johnson are recognized by this application.


from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import math


current_patient = None
current_caregiver = None


def create_patient(tokens):
    """
    This function creates patient's account. Patient needs to provide username and password to create an account.
    create_patient <username> <password>
    """

    # Check 1: the lengh for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    # check 2: check if the username has been already taken
    if username_exists_patient(username):
        print("Username taken, try again!")
        return
  
    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient account. 
    patient = Patient(username, salt=salt, hash=hash)

    # save patient information to the database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Create patient failed, Cannot save")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error:", e)
        return
    print(" *** Account created successfully *** ") 


def create_caregiver(tokens):
    '''
    This function creates caregiver's account. Caregiver needs to provide username and password to create an account.
    create_caregiver <username> <password>
    '''
    
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been already taken
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver account
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save caregiver information to the database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Create caregiver failed, Cannot save")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error:", e)
        return
    print(" *** Account created successfully *** ")


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    """
    This function lets a patient to log in, given the correct username and password.
    login_patient <username> <password>
    """

    # check 1: if someone's already logged-in, the person needs to log out first since the
    # system allows only one user to log in at a time.
    
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login patient failed")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when logging in. Please try again!")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Error occurred when logging in. Please try again!")
    else:
        print("Patient logged in as: " + username)
        current_patient = patient
   

def login_caregiver(tokens):
    '''
    This function lets a caregiver to log in, given the correct username and password.
    login_caregiver <username> <password>
    '''
    
    # check 1: if someone's already logged-in, the person needs to log out first since the
    # system allows only one user to log in at a time.
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login caregiver failed")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when logging in. Please try again!")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Error occurred when logging in. Please try again!")
    else:
        print("Caregiver logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    """
    This function outputs the usernames of the caregivers who are available on the specified date,
    along with the number of available doses left for each vaccine. 
    Both patients and caregivers can perform this operation.
    search_caregiver_schedule <date>
    
    """
    cm = ConnectionManager()
    conn = cm.create_connection()

    global current_caregiver
    global current_patient
    
    # check 1: Make sure that either a caregiver or a patient is logged in.
    if current_patient is None and current_caregiver is None:
       print("Please login first")
       return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]

    # check 3: Check the date is input in the correct format (mm-dd-yyyy).
    check_date = date.split('-')
    
    if len(check_date) != 3:
        print("Please enter a valid date in the format of 'MM-DD-YYYY'.") 
        return False
    
    if len(check_date[0]) != 2 or len(check_date[1]) != 2:
        print("Please enter a valid date in the format of 'MM-DD-YYYY'.")
        return False
    
    if len(check_date[2]) != 4:
        print("Please enter a valid date in the format of 'MM-DD-YYYY'.")
        return False
    
    
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])

    select_time = "SELECT Username FROM Availabilities WHERE Time = %s"
 
    try:
        cursor = conn.cursor(as_dict=True)
        schedule = datetime.datetime(year, month, day).strftime("%m-%d-%Y")
        cursor.execute(select_time, schedule)
        available = []
        
        for row in cursor:
            print('Available Caregiver:', row['Username'])
            available.append(row)
              
        if available:              
            cursor.execute("SELECT Name, Doses FROM Vaccines")
            for row in cursor:
                print('Available Vaccine:', row['Name'], '& Available Doses: ', row['Doses'])
                
        else:
            print('No Caregiver is available on the specified date. Please try another date.')
        cursor.close()
             
        
    except pymssql.Error as e:
        print("Search failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date in the format of 'MM-DD-YYYY'.")
        return
    except Exception as e:
        print("Error occurred when searching for caregiver's availability")
        print("Error:", e)
        return
    cm.close_connection()
    

def get_vaccine_info():
    '''
    This function returns the vaccine names and the corresponding number of available doses.
    '''
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)
    v_info = {"v_name": "v_dose"}

    get_all_vaccines = "SELECT Name, Doses FROM Vaccines"
    try:
        cursor.execute(get_all_vaccines)
        for row in cursor:
            v_info[str(row["Name"]).lower()] = row["Doses"]             
        return v_info
    
    except pymssql.Error:     
            print("Error occurred while obtaining vaccine information.")
            
    return
    cm.close_connection()


def get_appoint_id():
    '''
    This function generates the appointment ID.
    It finds the maximum ID number present in the database and assigns the next bigger integer.
    '''
    cm = ConnectionManager()
    conn = cm.create_connection()
    
    select_maxid = "SELECT MAX(AppointID) AS max_id FROM Appointments"

    try:
        cursor = conn.cursor()
        cursor.execute(select_maxid)
        maxid = cursor.fetchall()[0][0]
               
        if maxid is None:
            return 1
        
        else:
            maxid = int(maxid)
            return maxid + 1

    except pymssql.Error as e:
        print("Creating an appointment ID failed")
        print("Db-Error:", e)
        quit()
    except:
        print("Failed to create Appointment ID")
        return

    

def reserve(tokens):
    """
    Patients perform this operation to make an appointment.
    Once appointment is confirmed, an available caregiver will be randomly assigned.
    This function outputs the assigned caregiver and the appointment ID for the reservation.
    reserve <date> <vaccine>

    """
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    # check 1: check if the current logged-in user is a patient
    global current_patient
    if current_patient is None:
        print("Please login as a patient first!")
        return

    pname= current_patient.username
    
    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again! For Johnson & Johnson vaccine, please type 'Johnson'")
        return

    date = tokens[1]
    vaccine_name = tokens[2]

    # check 3: Check the date is input in the correct format (mm-dd-yyyy).
    check_date = date.split('-')
    
    if len(check_date) != 3:
        print("Please enter a valid date in the format of 'MM-DD-YYYY'.") 
        return False
    
    if len(check_date[0]) != 2 or len(check_date[1]) != 2:
        print("Please enter a valid date in the format of 'MM-DD-YYYY'.")
        return False
    
    if len(check_date[2]) != 4:
        print("Please enter a valid date in the format of 'MM-DD-YYYY'.")
        return False
    
    
    # check 4: Check if the correct vaccine name is input and it is available in stock.
    v_info = get_vaccine_info()
     
    if vaccine_name not in v_info:
        print('No such vaccine exists. Please corretly type the vaccine name.\nFor Johnson & Johnson vaccine, please type Johnson')
     
    elif math.isclose(v_info.get(vaccine_name), 0):
        print('Requested vaccine is out of stock. Please choose another vaccine.')

    else:      
        # assume input is hyphenated in the format mm-dd-yyyy
        date_tokens = date.split("-")
        month = int(date_tokens[0])
        day = int(date_tokens[1])
        year = int(date_tokens[2])

        
        
        # Make sure that a caregiver is available on the specified date. 
        select_caregiver = "SELECT Username FROM Availabilities WHERE Time = %s"
                      
        try:
            try:
                reservation = datetime.datetime(year, month, day).strftime("%m-%d-%Y")
                cursor.execute(select_caregiver, reservation)
                row = cursor.fetchone()
                assigned_caregiver = row["Username"]
                
                # Generate appointment ID's.
                appoint_id = get_appoint_id()
                print("Appointment confirmed! Assigned caregiver is:", assigned_caregiver,
                      "\nPlease print your appointment ID below and bring it with you. \n", appoint_id)

            except pymssql.Error as e:
                print("Making an appointment failed")
                print("Db-Error:", e)
                quit()
            except ValueError:
                print("Please enter a valid date in the format of 'MM-DD-YYYY'.")
                return                        
            except:
                print('No caregiver is available on the specified date.')
                return
     
            
            # After appointment has been confirmed, update the vaccine dose.  
            try:
                vaccine = Vaccine(vaccine_name, v_info.get(vaccine_name)).get()
                vaccine.decrease_available_doses(1)
            except:
                print("Error occursed while updating vaccine doses.")

            # Add appointment information to the database.
            add_appointment = "INSERT INTO Appointments VALUES (%d, %s, %s, %s, %s)"
            try:
                cursor.execute(add_appointment, (appoint_id, reservation, assigned_caregiver, current_patient.username, vaccine_name))
                conn.commit()
            except pymssql.Error:
                print("Error occured while updating appointment information")
                conn.rollback()
                cm.close_connection()
                return

            # Update caregiver's availability in the database.
            try:
                remove_availability = "DELETE FROM Availabilities WHERE Username = %s AND Time = %s"
                cursor.execute(remove_availability, (assigned_caregiver, reservation))
                conn.commit()
            except pymssql.Error:
                print("Error occured while updating caregiver availabilities")
                conn.rollback()
                cm.close_connection()
                return
                
        except pymssql.Error:
            print("Error occurred while making an appointment")
            conn.rollback()
            return
    cm.close_connection()    
   

def upload_availability(tokens):
    '''
    This function lets caregivers to upload their availability to the database.
    upload_availability <date>
    '''
    
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    """
    This function cancels an existing appointment. 
    Both caregivers and patients are able to cancel the appointment using this function. 
    Both of the patient’s and caregiver’s schedules should reflect the change made when the appointment is canceled.
    The patients and caregivers can only cancel their own appointments.
    cancel <appointment_id>
    """
    cm = ConnectionManager()
    conn = cm.create_connection()
    

    global current_caregiver
    global current_patient
    
    # Check 1: check if the token length is exactly 2. 
    if len(tokens) != 2:
        print("Please try again!")
        return

    appoint_id = tokens[1]
    
    # Check 2: Ensure that the specified appointment ID is the right type (integer).
    try:
        isinstance(int(appoint_id), int)
    except:
        print("Please input Appointment ID correctly. It should be an integer")
        return

    # Check 3: Check if either a caregiver or patient is logged in.
    if current_caregiver is None and current_patient is None:
        print("Please login first.")
        return
    
    # Identify the current user and set the requirement for cancelling appointment.  
    elif current_caregiver:
        req = f"Cname='{current_caregiver.username}'"
    else:
        req = f"Pname='{current_patient.username}'"
        

    appoint_details = f"""SELECT AppointID, Time, Cname, Pname, Vname FROM Appointments
                        WHERE AppointID = %d AND {req}"""
    try:
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(appoint_details, int(appoint_id))
            details = cursor.fetchone()
            date = details["Time"]
            cname = details["Cname"]
            pname = details["Pname"]
            vname = details["Vname"]
                      
        except:
            print("You do not have appointment scheduled with the specified appointment ID.")
            return

        # Caregivers and patients cannot cancel appointments other than their own.
        if cname is None or pname is None:
            print("You do not have appointment scheduled with the specified appointment ID.")   
        
        else:
            # Cancel appointment and update the database.
            delete_appoint = "DELETE FROM Appointments WHERE AppointID = %d"
            try:
                cursor = conn.cursor(as_dict=True)
                cursor.execute(delete_appoint, appoint_id)
                # Update caregiver's availability
                try:
                    add_avail = "INSERT INTO Availabilities VALUES (%s, %s)"
                    cursor = conn.cursor(as_dict=True)
                    cursor.execute(add_avail, (date.strftime("%Y-%m-%d"), cname))
                    conn.commit()
                except:
                    print('Attempt to update availability of caregiver failed.')
                    conn.rollback()
                    cm.close_connection()
                    return
            except pymssql.Error as e:
                print("Updating Availability Failed")

            # Update vaccine information
            try:
                v_info = get_vaccine_info()
                vaccine = Vaccine(vname, v_info.get(vname)).get()
                vaccine.increase_available_doses(1)

            except:
                print("Updating vaccine doses failed.")
                conn.rollback()
                cm.close_connection()
                return
    except pymssql.Error:
        print("Error occurred while cancelling appointment")
        cm.close_connection()
        return

    print("You have successfully cancelled your appointment.")
    cm.close_connection()    


def add_doses(tokens):
    '''
    This function allows caregivers to increase the number of vaccine doses.
    add_doses <vaccine> <number>    
    '''

    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Failed to get Vaccine information")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to get Vaccine information")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Failed to add new Vaccine to database")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Failed to add new Vaccine to database")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Failed to increase available doses for Vaccine")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Failed to increase available doses for Vaccine")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    '''
    This function outputs the scheduled appointment information for the current user (either a patient or a caregivers). 
    For caregivers, the appointment ID, vaccine name, date, and patient username are printed.
    For patients, the appointment ID, vaccine name, date, and caregiver username are printed.
    show_appointments
    '''
    global current_caregiver
    global current_patient
    
    # Check 1: Check if either a caregiver or a patient is logged in. 
    if current_caregiver is None and current_patient is None:
        print("Please log-in first")
        return

    # Check 2: the length for tokens need to be exactly 1.
    if len(tokens) != 1:
        print("Please try again!")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)
   
    # For caregivers, appointment ID, vaccine name, date, patient name should be printed.
    if current_caregiver:
        try:
           c_appoint = "SELECT * FROM Appointments WHERE Cname = %s"
           cursor.execute(c_appoint, current_caregiver.username)
           if cursor.rowcount == 0:
              print('No appointment has been scheduled.')                               
           else:
                for row in cursor:
                    print('Appointment ID:', row['AppointID'], '\nVaccine Name:', row['Vname'], '\nAppointment Date:', row['Time'],
                          '\nPatient Name:', row['Pname'], '\n')
              
        except pymssql.Error as e:
            print("Appointment Confirmation Failed")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Failed to retrieve appointment information.")
            return

    # For patients, appointment ID, vaccine name, date, caregiver name should be printed.
    elif current_patient:
        try:
            p_appoint = "SELECT * FROM Appointments WHERE Pname = %s"
            cursor.execute(p_appoint, current_patient.username)
            if cursor.rowcount == 0:
                print('No appointment has been scheduled.')
                return
            else:
                for row in cursor:
                    print('Appointment ID:', row['AppointID'], '\nVaccine Name:', row['Vname'], '\nAppointment Date:', row['Time'],
                          '\nCaregiver Name:', row['Cname'], '\n')

        except pymssql.Error as e:
            print("Appointment Confirmation Failed")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Failed to retrieve appointment information.")
            return

    else:
        print("Error occurred when confirming appointment. Please try again.")
        return
          


def logout(tokens):
    """
    This function allows the current user to log out.
    """
    global current_caregiver
    global current_patient

    # If caregiver is logged in:
    if current_caregiver is not None:
        current_caregiver = None
        print("You have been successfully logged out!")
        return

    # If patient is logged in:
    if current_patient is not None:
        current_patient = None
        print("You have been successfully logged out!!")
        return


def start():
    stop = False
    while not stop:
        print()
        print(" *** Please enter one of the following commands *** ")
        print("> create_patient <username> <password>")  
        print("> create_caregiver <username> <password>")
        print("> login_patient <username> <password>")  
        print("> login_caregiver <username> <password>")
        print("> search_caregiver_schedule <date>")  
        print("> reserve <date> <vaccine>") 
        print("> upload_availability <date>")
        print("> cancel <appointment_id>") 
        print("> add_doses <vaccine> <number>")
        print("> show_appointments")  
        print("> logout") 
        print("> Quit")
        print()
        response = ""
        print("> Enter: ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Type in a valid argument")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Try Again")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Thank you for using the scheduler, Goodbye!")
            stop = True
        else:
            print("Invalid Argument")


if __name__ == "__main__":
    
    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
