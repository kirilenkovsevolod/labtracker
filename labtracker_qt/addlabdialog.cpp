#include "addlabdialog.h"

AddLabDialog::AddLabDialog(QWidget *parent)
    : QDialog(parent)
{
    m_network = new QNetworkAccessManager(this);

    setWindowTitle("Назначить лабораторную");
    setMinimumSize(480, 400);

    QFormLayout *form = new QFormLayout();

    // Выбор шаблона
    m_templateCombo = new QComboBox(this);
    m_templateCombo->addItem("Загрузка...");
    form->addRow("Лабораторная:", m_templateCombo);

    // Группа
    m_groupEdit = new QLineEdit(this);
    m_groupEdit->setPlaceholderText("Например: РИС-25-3Б");
    form->addRow("Группа:", m_groupEdit);

    // Дедлайн
    m_deadlineEdit = new QDateEdit(this);
    m_deadlineEdit->setDate(QDate::currentDate().addDays(14));
    m_deadlineEdit->setCalendarPopup(true);
    m_deadlineEdit->setDisplayFormat("yyyy-MM-dd");
    form->addRow("Дедлайн:", m_deadlineEdit);

    // Содержание (только для просмотра)
    m_contentView = new QTextEdit(this);
    m_contentView->setReadOnly(true);
    m_contentView->setMaximumHeight(80);
    m_contentView->setPlaceholderText("Содержание лабораторной...");
    form->addRow("Содержание:", m_contentView);

    // Вопросы
    m_questionsLabel = new QLabel("", this);
    m_questionsLabel->setWordWrap(true);
    m_questionsLabel->setStyleSheet("color: gray; font-size: 11px;");
    form->addRow("Вопросы:", m_questionsLabel);

    // Кнопки
    m_submitBtn = new QPushButton("Назначить", this);
    m_cancelBtn = new QPushButton("Отмена", this);
    QHBoxLayout *btnLayout = new QHBoxLayout();
    btnLayout->addStretch();
    btnLayout->addWidget(m_cancelBtn);
    btnLayout->addWidget(m_submitBtn);

    QVBoxLayout *main = new QVBoxLayout(this);
    main->addLayout(form);
    main->addStretch();
    main->addLayout(btnLayout);

    connect(m_templateCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, &AddLabDialog::onTemplateSelected);
    connect(m_submitBtn, &QPushButton::clicked, this, &AddLabDialog::onSubmit);
    connect(m_cancelBtn, &QPushButton::clicked, this, &QDialog::reject);

    loadTemplates();
}

void AddLabDialog::loadTemplates()
{
    QNetworkRequest req(QUrl(API + "/lab_templates"));
    QNetworkReply *reply = m_network->get(req);
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        onTemplatesLoaded(reply);
    });
}

void AddLabDialog::onTemplatesLoaded(QNetworkReply *reply)
{
    reply->deleteLater();
    if (reply->error() != QNetworkReply::NoError) {
        m_templateCombo->clear();
        m_templateCombo->addItem("Ошибка загрузки");
        return;
    }

    m_templates = QJsonDocument::fromJson(reply->readAll()).array();
    m_templateCombo->clear();
    m_templateCombo->addItem("-- Выберите лабораторную --");

    for (const QJsonValue &v : m_templates) {
        m_templateCombo->addItem(v.toObject()["title"].toString());
    }
}

void AddLabDialog::onTemplateSelected(int index)
{
    // index 0 — заглушка
    if (index <= 0 || index - 1 >= m_templates.size()) {
        m_contentView->clear();
        m_questionsLabel->clear();
        return;
    }

    QJsonObject tmpl = m_templates[index - 1].toObject();
    m_contentView->setText(tmpl["content"].toString());

    QJsonArray questions = tmpl["questions"].toArray();
    QString qText;
    int i = 1;
    for (const QJsonValue &q : questions) {
        qText += QString("%1. %2\n").arg(i++).arg(q.toString());
    }
    m_questionsLabel->setText(qText);
}

void AddLabDialog::onSubmit()
{
    int idx = m_templateCombo->currentIndex();
    if (idx <= 0) {
        QMessageBox::warning(this, "Ошибка", "Выберите лабораторную");
        return;
    }
    if (m_groupEdit->text().trimmed().isEmpty()) {
        QMessageBox::warning(this, "Ошибка", "Введите группу");
        return;
    }

    m_submitBtn->setEnabled(false);

    QJsonObject json;
    json["title"]      = m_templateCombo->currentText();
    json["group_name"] = m_groupEdit->text().trimmed();
    json["content"]    = m_contentView->toPlainText();
    json["deadline"]   = m_deadlineEdit->date().toString("yyyy-MM-dd");

    QNetworkRequest req(QUrl(API + "/lab"));
    req.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

    QNetworkReply *reply = m_network->post(req, QJsonDocument(json).toJson());
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        onReplyFinished(reply);
    });
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
    accept();
}
