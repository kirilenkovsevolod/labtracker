QT += core gui widgets network

CONFIG += c++17

TARGET = labtracker
TEMPLATE = app

SOURCES += \
    main.cpp \
    mainwindow.cpp \
    addlabdialog.cpp \
    addstudentdialog.cpp

HEADERS += \
    mainwindow.h \
    addlabdialog.h \
    addstudentdialog.h
