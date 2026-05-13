#include <QApplication>
#include "mainwindow.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);

    app.setStyle("Fusion"); // чистый кроссплатформенный стиль

    MainWindow w;
    w.show();

    return app.exec();
}
