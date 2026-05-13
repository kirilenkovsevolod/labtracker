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
#include <QJsonDocument>
#include <QJsonObject>
#include <QMessageBox>
#include <QUrlQuery>

class AddLabDialog : public QDialog
{
    Q_OBJECT

public:
    explicit AddLabDialog(QWidget *parent = nullptr);

signals:
    void labAdded(); // сигнал после успешного добавления

private slots:
    void onSubmit();
    void onReplyFinished(QNetworkReply *reply);

private:
    QLineEdit *m_titleEdit;
    QLineEdit *m_groupEdit;
    QPushButton *m_submitBtn;
    QPushButton *m_cancelBtn;
    QNetworkAccessManager *m_network;

    const QString API = "http://127.0.0.1:8000";
};
