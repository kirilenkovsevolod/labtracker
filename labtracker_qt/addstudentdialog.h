#pragma once

#include <QDialog>
#include <QLineEdit>
#include <QPushButton>
#include <QFormLayout>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QMessageBox>
#include <QUrlQuery>

class AddStudentDialog : public QDialog
{
    Q_OBJECT

public:
    explicit AddStudentDialog(QWidget *parent = nullptr);

signals:
    void studentAdded();

private slots:
    void onSubmit();
    void onReplyFinished(QNetworkReply *reply);

private:
    QLineEdit *m_nameEdit;
    QLineEdit *m_loginEdit;
    QLineEdit *m_passwordEdit;
    QLineEdit *m_groupEdit;

    QPushButton *m_submitBtn;
    QPushButton *m_cancelBtn;

    QNetworkAccessManager *m_network;

    const QString API = "http://127.0.0.1:8000";
};
