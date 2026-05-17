#pragma once

#include <QMainWindow>
#include <QTabWidget>
#include <QTableWidget>
#include <QPushButton>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QLabel>
#include <QStatusBar>
#include <QList>
#include <QMessageBox>
#include <QFileDialog>
#include <QHttpMultiPart>
#include <QHttpPart>
#include <QFile>
#include <QMimeDatabase>

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);

private slots:
    void refreshAll();
    void openAddLabDialog();
    void openAddStudentDialog();
    void deleteSelectedLab();
    void deleteSelectedStudent();
    void deleteSelectedSubmission();
    void uploadFileForSelectedLab();

    void onStudentsLoaded(QNetworkReply *reply);
    void onLabsLoaded(QNetworkReply *reply);
    void onSubmissionsLoaded(QNetworkReply *reply);

private:
    void setupUi();
    void setupStudentsTab();
    void setupLabsTab();
    void setupSubmissionsTab();
    void sendDelete(const QString &url, std::function<void()> onSuccess);

    QNetworkAccessManager *m_network;
    QTabWidget  *m_tabs;

    // Студенты
    QTableWidget *m_studentsTable;
    QPushButton  *m_addStudentBtn;
    QPushButton  *m_deleteStudentBtn;
    QList<int>    m_studentIds;

    // Лабораторные
    QTableWidget *m_labsTable;
    QPushButton  *m_addLabBtn;
    QPushButton  *m_deleteLabBtn;
    QPushButton  *m_uploadFileBtn;
    QList<int>    m_labIds;

    // Сдачи
    QTableWidget *m_submissionsTable;
    QPushButton  *m_deleteSubmissionBtn;
    QList<int>    m_submissionIds;

    const QString API = "http://127.0.0.1:8000";
};
