import QtQuick 6.2
import QtQuick.Controls 6.2
import Appka
import QtQuick.Layouts 6.3
import QtQuick.Studio.Components 1.0
import QtQuick.Studio.MultiText 1.0

Rectangle {
    width: 720
    height: 720
    color: "#414141"

    scale: 1

    Button {
        id: button
        x: 49
        y: 599
        width: 160
        height: 80
        text: qsTr("START")
        font.pointSize: 20
        display: AbstractButton.TextBesideIcon
        icon.color: "#ffffff"
        scale: 1
    }

    ProgressBar {
        id: progressBar
        x: 246
        y: 659
        width: 427
        height: 20
        value: 0.5
    }

    Text {
        id: text1
        x: 246
        y: 599
        width: 300
        height: 50
        color: "#ffffff"
        text: qsTr("Progress...")
        font.pixelSize: 30
    }

    TextField {
        id: textField
        x: 246
        y: 102
        width: 300
        height: 30
        placeholderText: qsTr("Text Field")
    }

    Text {
        id: text2
        x: 49
        y: 102
        width: 150
        height: 30
        color: "#ffffff"
        text: qsTr("Save folder :")
        font.pixelSize: 20
        horizontalAlignment: Text.AlignRight
    }

    TextField {
        id: textField1
        x: 246
        y: 174
        width: 100
        height: 30
        placeholderText: qsTr("Text Field")
    }

    Text {
        id: text3
        x: 49
        y: 174
        width: 150
        height: 30
        color: "#ffffff"
        text: qsTr("Sample rate :")
        font.pixelSize: 20
        horizontalAlignment: Text.AlignRight
    }

    TextField {
        id: textField2
        x: 246
        y: 210
        width: 100
        height: 30
        placeholderText: qsTr("Text Field")
    }

    Text {
        id: text4
        x: 49
        y: 210
        width: 150
        height: 30
        color: "#ffffff"
        text: qsTr("Time to measure :")
        font.pixelSize: 20
        horizontalAlignment: Text.AlignRight
    }

    GroupItem {
        id: group
        x: -45
        y: 563
    }

    Button {
        id: button1
        x: 573
        y: 102
        text: qsTr("Select folder")
    }

    Text {
        id: text5
        x: 352
        y: 210
        width: 150
        height: 30
        color: "#ffffff"
        text: qsTr("seconds")
        font.pixelSize: 20
    }

    Text {
        id: text6
        x: 352
        y: 174
        width: 150
        height: 30
        color: "#ffffff"
        text: qsTr("hz")
        font.pixelSize: 20
    }

    TextField {
        id: textField3
        x: 246
        y: 66
        width: 300
        height: 30
        placeholderText: qsTr("Text Field")
    }

    Text {
        id: text7
        x: 49
        y: 66
        width: 150
        height: 30
        color: "#ffffff"
        text: qsTr("File name :")
        font.pixelSize: 20
        horizontalAlignment: Text.AlignRight
    }

    Button {
        id: button2
        x: 49
        y: 266
        text: qsTr("SAVE CONFIG")
    }
}
