CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Availabilities (
    Time date,
    Username varchar(255) REFERENCES Caregivers,
    PRIMARY KEY (Time, Username)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);
    
CREATE TABLE Patients (
    Username varchar(255),  
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Appointments (
    AppointID int,  
    Time date,
    Cname varchar(255) REFERENCES Caregivers(Username),
    Pname varchar(255) REFERENCES Patients(Username),
    Vname varchar(255) REFERENCES Vaccines(Name),
    PRIMARY KEY (AppointID)
);