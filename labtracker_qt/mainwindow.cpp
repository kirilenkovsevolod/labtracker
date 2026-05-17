#include "mainwindow.h"
#include "addlabdialog.h"
#include "addstudentdialog.h"
#include <QUrl>
#include <QHeaderView>
#include <functional>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    m_network = new QNetworkAccessManager(this);
    setupUi();
    refreshAll();
}

void MainWindow::setupUi()
{
    setWindowTitle("LabTracker — Панель преподавателя");
    resize(900, 620);

    QWidget *central = new QWidget(this);
    QVBoxLayout *rootLayout = new QVBoxLayout(central);
    rootLayout->setContentsMargins(10, 10, 10, 10);
    rootLayout->setSpacing(8);

    QHBoxLayout *topBar = new QHBoxLayout();
    QLabel *titleLabel = new QLabel("<b>LabTracker</b>", this);
    titleLabel->setStyleSheet("font-size: 16px;");
    QPushButton *refreshBtn = new QPushButton("🔄 Обновить данные", this);
    refreshBtn->setFixedWidth(180);
    topBar->addWidget(titleLabel);
    topBar->addStretch();
    topBar->addWidget(refreshBtn);
    connect(refreshBtn, &QPushButton::clicked, this, &MainWindow::refreshAll);

    m_tabs = new QTabWidget(this);
    setupStudentsTab();
    setupLabsTab();
    setupSubmissionsTab();

    rootLayout->addLayout(topBar);
    rootLayout->addWidget(m_tabs);
    setCentralWidget(central);
    statusBar()->showMessage("Готово");
}

void MainWindow::setupStudentsTab()
{
    QWidget *tab = new QWidget();
    QVBoxLayout *layout = new QVBoxLayout(tab);

    QHBoxLayout *btnRow = new QHBoxLayout();
    m_addStudentBtn = new QPushButton("+ Добавить студента", tab);
    m_addStudentBtn->setFixedWidth(200);
    m_deleteStudentBtn = new QPushButton("🗑 Удалить выбранного", tab);
    m_deleteStudentBtn->setFixedWidth(200);
    m_deleteStudentBtn->setEnabled(false);
    btnRow->addWidget(m_addStudentBtn);
    btnRow->addWidget(m_deleteStudentBtn);
    btnRow->addStretch();

    connect(m_addStudentBtn,    &QPushButton::clicked, this, &MainWindow::openAddStudentDialog);
    connect(m_deleteStudentBtn, &QPushButton::clicked, this, &MainWindow::deleteSelectedStudent);

    m_studentsTable = new QTableWidget(0, 3, tab);
    m_studentsTable->setHorizontalHeaderLabels({"Имя", "Группа", "Telegram ID"});
    m_studentsTable->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    m_studentsTable->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_studentsTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_studentsTable->verticalHeader()->setVisible(false);

    connect(m_studentsTable, &QTableWidget::itemSelectionChanged, this, [this]() {
        m_deleteStudentBtn->setEnabled(m_studentsTable->currentRow() >= 0);
    });

    layout->addLayout(btnRow);
    layout->addWidget(m_studentsTable);
    m_tabs->addTab(tab, "👤 Студенты");
}

void MainWindow::setupLabsTab()
{
    QWidget *tab = new QWidget();
    QVBoxLayout *layout = new QVBoxLayout(tab);

    QHBoxLayout *btnRow = new QHBoxLayout();
    m_addLabBtn = new QPushButton("+ Добавить лабораторную", tab);
    m_addLabBtn->setFixedWidth(220);
    m_deleteLabBtn = new QPushButton("🗑 Удалить", tab);
    m_deleteLabBtn->setFixedWidth(120);
    m_deleteLabBtn->setEnabled(false);
    m_uploadFileBtn = new QPushButton("📎 Прикрепить файл", tab);
    m_uploadFileBtn->setFixedWidth(180);
    m_uploadFileBtn->setEnabled(false);

    btnRow->addWidget(m_addLabBtn);
    btnRow->addWidget(m_deleteLabBtn);
    btnRow->addWidget(m_uploadFileBtn);
    btnRow->addStretch();

    connect(m_addLabBtn,    &QPushButton::clicked, this, &MainWindow::openAddLabDialog);
    connect(m_deleteLabBtn, &QPushButton::clicked, this, &MainWindow::deleteSelectedLab);
    connect(m_uploadFileBtn,&QPushButton::clicked, this, &MainWindow::uploadFileForSelectedLab);

    m_labsTable = new QTableWidget(0, 3, tab);
    m_labsTable->setHorizontalHeaderLabels({"Название", "Группа", "Файл"});
    m_labsTable->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    m_labsTable->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_labsTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_labsTable->verticalHeader()->setVisible(false);

    connect(m_labsTable, &QTableWidget::itemSelectionChanged, this, [this]() {
        bool selected = m_labsTable->currentRow() >= 0;
        m_deleteLabBtn->setEnabled(selected);
        m_uploadFileBtn->setEnabled(selected);
    });

    layout->addLayout(btnRow);
    layout->addWidget(m_labsTable);
    m_tabs->addTab(tab, "📚 Лабораторные");
}

void MainWindow::setupSubmissionsTab()
{
    QWidget *tab = new QWidget();
    QVBoxLayout *layout = new QVBoxLayout(tab);

    QHBoxLayout *btnRow = new QHBoxLayout();
    m_deleteSubmissionBtn = new QPushButton("🗑 Удалить выбранную сдачу", tab);
    m_deleteSubmissionBtn->setFixedWidth(220);
    m_deleteSubmissionBtn->setEnabled(false);
    btnRow->addWidget(m_deleteSubmissionBtn);
    btnRow->addStretch();

    connect(m_deleteSubmissionBtn, &QPushButton::clicked, this, &MainWindow::deleteSelectedSubmission);

    m_submissionsTable = new QTableWidget(0, 3, tab);
    m_submissionsTable->setHorizontalHeaderLabels({"Студент", "Лабораторная", "Статус"});
    m_submissionsTable->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    m_submissionsTable->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_submissionsTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_submissionsTable->verticalHeader()->setVisible(false);

    connect(m_submissionsTable, &QTableWidget::itemSelectionChanged, this, [this]() {
        m_deleteSubmissionBtn->setEnabled(m_submissionsTable->currentRow() >= 0);
    });

    layout->addLayout(btnRow);
    layout->addWidget(m_submissionsTable);
    m_tabs->addTab(tab, "✅ Сдачи");
}

// ─── Сеть ────────────────────────────────────────────────────────────────────

void MainWindow::refreshAll()
{
    statusBar()->showMessage("Загрузка...");

    {
        QNetworkRequest req(QUrl(API + "/students"));
        QNetworkReply *reply = m_network->get(req);
        connect(reply, &QNetworkReply::finished, this, [this, reply]() { onStudentsLoaded(reply); });
    }
    {
        QNetworkRequest req(QUrl(API + "/labs_all"));
        QNetworkReply *reply = m_network->get(req);
        connect(reply, &QNetworkReply::finished, this, [this, reply]() { onLabsLoaded(reply); });
    }
    {
        QNetworkRequest req(QUrl(API + "/submissions"));
        QNetworkReply *reply = m_network->get(req);
        connect(reply, &QNetworkReply::finished, this, [this, reply]() { onSubmissionsLoaded(reply); });
    }
}

void MainWindow::sendDelete(const QString &url, std::function<void()> onSuccess)
{
    QUrl qurl(url);
    QNetworkRequest req(qurl);
    QNetworkReply *reply = m_network->deleteResource(req);
    connect(reply, &QNetworkReply::finished, this, [this, reply, onSuccess]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            QMessageBox::critical(this, "Ошибка", "Не удалось удалить:\n" + reply->errorString());
            return;
        }
        onSuccess();
    });
}

void MainWindow::onStudentsLoaded(QNetworkReply *reply)
{
    reply->deleteLater();
    if (reply->error() != QNetworkReply::NoError) { statusBar()->showMessage("Ошибка загрузки студентов"); return; }
    QJsonArray arr = QJsonDocument::fromJson(reply->readAll()).array();
    m_studentsTable->setRowCount(0);
    m_studentIds.clear();
    for (const QJsonValue &v : arr) {
        QJsonObject obj = v.toObject();
        int row = m_studentsTable->rowCount();
        m_studentsTable->insertRow(row);
        m_studentsTable->setItem(row, 0, new QTableWidgetItem(obj["name"].toString()));
        m_studentsTable->setItem(row, 1, new QTableWidgetItem(obj["group_name"].toString()));
        m_studentsTable->setItem(row, 2, new QTableWidgetItem(
            QString::number(obj["telegram_id"].toVariant().toLongLong())));
        m_studentIds.append(obj["id"].toInt());
    }
    m_deleteStudentBtn->setEnabled(false);
    statusBar()->showMessage("Данные обновлены");
}

void MainWindow::onLabsLoaded(QNetworkReply *reply)
{
    reply->deleteLater();
    if (reply->error() != QNetworkReply::NoError) { statusBar()->showMessage("Ошибка загрузки лаб"); return; }
    QJsonArray arr = QJsonDocument::fromJson(reply->readAll()).array();
    m_labsTable->setRowCount(0);
    m_labIds.clear();
    for (const QJsonValue &v : arr) {
        QJsonObject obj = v.toObject();
        int row = m_labsTable->rowCount();
        m_labsTable->insertRow(row);
        m_labsTable->setItem(row, 0, new QTableWidgetItem(obj["title"].toString()));
        m_labsTable->setItem(row, 1, new QTableWidgetItem(obj["group_name"].toString()));
        QString fp = obj["file_path"].toString();
        m_labsTable->setItem(row, 2, new QTableWidgetItem(fp.isEmpty() ? "—" : "✅ Есть"));
        m_labIds.append(obj["id"].toInt());
    }
    m_deleteLabBtn->setEnabled(false);
    m_uploadFileBtn->setEnabled(false);
}

void MainWindow::onSubmissionsLoaded(QNetworkReply *reply)
{
    reply->deleteLater();
    if (reply->error() != QNetworkReply::NoError) { statusBar()->showMessage("Ошибка загрузки сдач"); return; }
    QJsonArray arr = QJsonDocument::fromJson(reply->readAll()).array();
    m_submissionsTable->setRowCount(0);
    m_submissionIds.clear();
    for (const QJsonValue &v : arr) {
        QJsonObject obj = v.toObject();
        int row = m_submissionsTable->rowCount();
        m_submissionsTable->insertRow(row);
        m_submissionsTable->setItem(row, 0, new QTableWidgetItem(obj["student_name"].toString()));
        m_submissionsTable->setItem(row, 1, new QTableWidgetItem(obj["lab_title"].toString()));
        QString status = obj["status"].toString();
        QString icon = (status == "done") ? "✅ Сдано" : "⏳ На проверке";
        QTableWidgetItem *si = new QTableWidgetItem(icon);
        si->setForeground((status == "done") ? Qt::darkGreen : Qt::darkYellow);
        m_submissionsTable->setItem(row, 2, si);
        m_submissionIds.append(obj["id"].toInt());
    }
    m_deleteSubmissionBtn->setEnabled(false);
}

// ─── Загрузка файла ───────────────────────────────────────────────────────────

void MainWindow::uploadFileForSelectedLab()
{
    int row = m_labsTable->currentRow();
    if (row < 0 || row >= m_labIds.size()) return;

    QString filePath = QFileDialog::getOpenFileName(
        this, "Выберите файл лабораторной", "",
        "Документы (*.pdf *.docx *.doc *.txt);;Все файлы (*)"
    );
    if (filePath.isEmpty()) return;

    int labId = m_labIds[row];
    QString labTitle = m_labsTable->item(row, 0)->text();

    QFile *file = new QFile(filePath);
    if (!file->open(QIODevice::ReadOnly)) {
        QMessageBox::critical(this, "Ошибка", "Не удалось открыть файл");
        delete file;
        return;
    }

    QHttpMultiPart *multiPart = new QHttpMultiPart(QHttpMultiPart::FormDataType);

    QHttpPart filePart;
    QFileInfo fi(filePath);
    filePart.setHeader(QNetworkRequest::ContentDispositionHeader,
        QString("form-data; name=\"file\"; filename=\"%1\"").arg(fi.fileName()));
    filePart.setHeader(QNetworkRequest::ContentTypeHeader, "application/octet-stream");
    filePart.setBodyDevice(file);
    file->setParent(multiPart);

    multiPart->append(filePart);

    QUrl qurl(API + QString("/lab/%1/upload").arg(labId));
    QNetworkRequest req(qurl);
    QNetworkReply *reply = m_network->post(req, multiPart);
    multiPart->setParent(reply);

    statusBar()->showMessage("Загрузка файла...");

    connect(reply, &QNetworkReply::finished, this, [this, reply, labTitle]() {
        reply->deleteLater();
        if (reply->error() != QNetworkReply::NoError) {
            QMessageBox::critical(this, "Ошибка", "Не удалось загрузить файл:\n" + reply->errorString());
            return;
        }
        statusBar()->showMessage(QString("Файл для \"%1\" загружен").arg(labTitle));
        refreshAll();
    });
}

// ─── Удаление ────────────────────────────────────────────────────────────────

void MainWindow::deleteSelectedLab()
{
    int row = m_labsTable->currentRow();
    if (row < 0 || row >= m_labIds.size()) return;
    QString title = m_labsTable->item(row, 0)->text();
    if (QMessageBox::question(this, "Удалить", QString("Удалить \"%1\"?").arg(title),
            QMessageBox::Yes | QMessageBox::No) != QMessageBox::Yes) return;
    sendDelete(API + QString("/lab/%1").arg(m_labIds[row]), [this]() {
        statusBar()->showMessage("Лабораторная удалена"); refreshAll();
    });
}

void MainWindow::deleteSelectedStudent()
{
    int row = m_studentsTable->currentRow();
    if (row < 0 || row >= m_studentIds.size()) return;
    QString name = m_studentsTable->item(row, 0)->text();
    if (QMessageBox::question(this, "Удалить", QString("Удалить \"%1\"?").arg(name),
            QMessageBox::Yes | QMessageBox::No) != QMessageBox::Yes) return;
    sendDelete(API + QString("/student/%1").arg(m_studentIds[row]), [this]() {
        statusBar()->showMessage("Студент удалён"); refreshAll();
    });
}

void MainWindow::deleteSelectedSubmission()
{
    int row = m_submissionsTable->currentRow();
    if (row < 0 || row >= m_submissionIds.size()) return;
    if (QMessageBox::question(this, "Удалить", "Удалить эту сдачу?",
            QMessageBox::Yes | QMessageBox::No) != QMessageBox::Yes) return;
    sendDelete(API + QString("/submission/%1").arg(m_submissionIds[row]), [this]() {
        statusBar()->showMessage("Сдача удалена"); refreshAll();
    });
}

// ─── Диалоги ─────────────────────────────────────────────────────────────────

void MainWindow::openAddLabDialog()
{
    AddLabDialog *dlg = new AddLabDialog(this);
    connect(dlg, &AddLabDialog::labAdded, this, &MainWindow::refreshAll);
    dlg->exec();
}

void MainWindow::openAddStudentDialog()
{
    AddStudentDialog *dlg = new AddStudentDialog(this);
    connect(dlg, &AddStudentDialog::studentAdded, this, &MainWindow::refreshAll);
    dlg->exec();
}
