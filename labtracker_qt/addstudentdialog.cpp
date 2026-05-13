#include "addstudentdialog.h"

AddStudentDialog::AddStudentDialog(QWidget *parent)
    : QDialog(parent)
{
    m_network = new QNetworkAccessManager(this);

    setWindowTitle("Добавить студента");
    setFixedSize(360, 200);

    QFormLayout *form = new QFormLayout();

    m_nameEdit = new QLineEdit(this);
    m_nameEdit->setPlaceholderText("Например: Павел");

    m_loginEdit = new QLineEdit(this);
    m_loginEdit->setPlaceholderText("Например: pavel");

    m_passwordEdit = new QLineEdit(this);
    m_passwordEdit->setPlaceholderText("Пароль");
    m_passwordEdit->setEchoMode(QLineEdit::Password);

    m_groupEdit = new QLineEdit(this);
    m_groupEdit->setPlaceholderText("Например: РИС-25-3Б");

    form->addRow("Имя:", m_nameEdit);
    form->addRow("Логин:", m_loginEdit);
    form->addRow("Пароль:", m_passwordEdit);
    form->addRow("Группа:", m_groupEdit);

    m_submitBtn = new QPushButton("Добавить", this);
    m_cancelBtn = new QPushButton("Отмена", this);

    QHBoxLayout *btnLayout = new QHBoxLayout();
    btnLayout->addStretch();
    btnLayout->addWidget(m_cancelBtn);
    btnLayout->addWidget(m_submitBtn);

    QVBoxLayout *main = new QVBoxLayout(this);
    main->addLayout(form);
    main->addStretch();
    main->addLayout(btnLayout);

    connect(m_submitBtn, &QPushButton::clicked, this, &AddStudentDialog::onSubmit);
    connect(m_cancelBtn, &QPushButton::clicked, this, &QDialog::reject);
    connect(m_network, &QNetworkAccessManager::finished, this, &AddStudentDialog::onReplyFinished);
}

void AddStudentDialog::onSubmit()
{
    QString name     = m_nameEdit->text().trimmed();
    QString login    = m_loginEdit->text().trimmed();
    QString password = m_passwordEdit->text().trimmed();
    QString group    = m_groupEdit->text().trimmed();

    if (name.isEmpty() || login.isEmpty() || password.isEmpty() || group.isEmpty()) {
        QMessageBox::warning(this, "Ошибка", "Заполните все поля");
        return;
    }

    m_submitBtn->setEnabled(false);

    QUrlQuery query;
    query.addQueryItem("name",       name);
    query.addQueryItem("login",      login);
    query.addQueryItem("password",   password);
    query.addQueryItem("group_name", group);

    QUrl url(API + "/student");
    url.setQuery(query);

    QNetworkRequest req(url);
    m_network->post(req, QByteArray());
}

void AddStudentDialog::onReplyFinished(QNetworkReply *reply)
{
    reply->deleteLater();
    m_submitBtn->setEnabled(true);

    if (reply->error() != QNetworkReply::NoError) {
        QMessageBox::critical(this, "Ошибка",
            "Не удалось добавить студента:\n" + reply->errorString());
        return;
    }

    emit studentAdded();
    accept();
}
