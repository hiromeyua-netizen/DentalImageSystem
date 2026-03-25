import QtQuick

// Circular numbered chip.  Tap → tapped(i).  Hold 700 ms → longPress(i).
Rectangle {
    id: chip
    property int  chipIndex: 0
    property bool isActive:  false

    signal tapped(int i)
    signal longPress(int i)

    width: 44; height: 44; radius: 22
    color:        isActive ? Qt.rgba(1,1,1,0.18) : "transparent"
    border.width: 1.5
    border.color: isActive ? Qt.rgba(1,1,1,0.80) : Qt.rgba(1,1,1,0.40)

    Behavior on color        { ColorAnimation { duration: 160 } }
    Behavior on border.color { ColorAnimation { duration: 160 } }

    Text {
        anchors.centerIn: parent
        text:  chip.chipIndex + 1
        font.pixelSize: 16; font.weight: Font.Medium
        color: chip.isActive ? "#ffffff" : Qt.rgba(1,1,1,0.70)
    }

    scale: ma.pressed ? 0.86 : 1.0
    Behavior on scale { NumberAnimation { duration: 85; easing.type: Easing.OutBack } }

    property bool _fired: false
    Timer { id: t; interval: 700; onTriggered: { chip._fired = true; chip.longPress(chip.chipIndex) } }

    MouseArea {
        id: ma; anchors.fill: parent; cursorShape: Qt.PointingHandCursor
        onPressed:  { chip._fired = false; t.start() }
        onReleased: { t.stop(); if (!chip._fired) chip.tapped(chip.chipIndex) }
        onCanceled: t.stop()
    }
}
