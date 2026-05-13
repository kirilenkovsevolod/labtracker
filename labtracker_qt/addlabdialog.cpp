#include "addlabdialog.h"

AddLabDialog::AddLabDialog(QWidget *parent)
    : QDialog(parent)
{
    m_network = new QNetworkAccessManager(this);

    setWindowTitle("Добавить лабораторную");
    setFixedSize(340, 160);

    QFormLayout *form = new QFormLayout();
    m_titleEdit = new QLineEdit(this);
    m_titleEdit->setPlaceholderText("Например: Лабораторная 4");
    m_groupEdit = new QLineEdit(this);
    m_groupEdit->setPlaceholderText("Например: РИС-25-3Б");
    form->addRow("Название:", m_titleEdit);
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

    connect(m_submitBtn, &QPushButton::clicked, this, &AddLabDialog::onSubmit);
    connect(m_cancelBtn, &QPushButton::clicked, this, &QDialog::reject);
    connect(m_network, &QNetworkAccessManager::finished, this, &AddLabDialog::onReplyFinished);
}

void AddLabDialog::onSubmit()
{
    QString title = m_titleEdit->text().trimmed();
    QString group = m_groupEdit->text().trimmed();

    if (title.isEmpty() || group.isEmpty()) {
        QMessageBox::warning(this, "Ошибка", "Заполните все поля");
        return;
    }

    m_submitBtn->setEnabled(false);

    QUrlQuery query;
    query.addQueryItem("title", title);
    query.addQueryItem("group_name", group);

    QUrl url(API + "/lab");
    url.setQuery(query);

    QNetworkRequest req(url);
    m_network->post(req, QByteArray()); // тело пустое — параметры в query
}

void AddLabDialog::onReplyFinished(QNetworkReply *reply)
{
    reply->deleteLater();
    m_submitBtn->setEnabled(true);

    if (reply->error() != QNetworkReply::NoError) {
        QMessageBox::critical(this, "Ошибка", "Не удалось добавить лабораторную:\n" + reply->errorString());
        return;
    }

    emit labAdded();
    accept(); // закрыть диалог
}
