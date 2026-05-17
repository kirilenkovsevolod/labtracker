#pragma once

#include <QDialog>
#include <QLineEdit>
#include <QPushButton>
#include <QComboBox>
#include <QDateEdit>
#include <QTextEdit>
#include <QLabel>
#include <QFormLayout>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QMessageBox>
#include <QUrlQuery>
#include <QDate>

class AddLabDialog : public QDialog
{
    Q_OBJECT

public:
    explicit AddLabDialog(QWidget *parent = nullptr);

signals:
    void labAdded();

private slots:
    void onTemplateSelected(int index);
    void onSubmit();
    void onTemplatesLoaded(QNetworkReply *reply);
    void onReplyFinished(QNetworkReply *reply);

private:
    void loadTemplates();

    QComboBox  *m_templateCombo;
    QLineEdit  *m_groupEdit;
    QDateEdit  *m_deadlineEdit;
    QTextEdit  *m_contentView;   // только для просмотра
    QLabel     *m_questionsLabel;

    QPushButton *m_submitBtn;
    QPushButton *m_cancelBtn;

    QNetworkAccessManager *m_network;

    // данные шаблонов
    QJsonArray m_templates;

    const QString API = "http://127.0.0.1:8000";
};
