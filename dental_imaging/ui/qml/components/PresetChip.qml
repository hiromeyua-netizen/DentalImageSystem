import QtQuick

// Circular preset chip — tap to apply, long-press (~700 ms) to save.
Rectangle {
    id: chip

    property int  chipIndex: 0
    property bool isActive:  false

    signal tapped(int i)
    signal longPress(int i)

    width:        52
    height:       52
    radius:       26
    color:        isActive ? Qt.rgba(1, 1, 1, 0.22) : "transparent"
    border.width: 2
    border.color: isActive ? Qt.rgba(1, 1, 1, 0.80) : Qt.rgba(1, 1, 1, 0.45)

    Behavior on color        { ColorAnimation { duration: 180 } }
    Behavior on border.color { ColorAnimation { duration: 180 } }

    Text {
        anchors.centerIn: parent
        text:             chip.chipIndex + 1
        font.pixelSize:   18
        font.weight:      Font.Medium
        color:            chip.isActive ? "#ffffff" : Qt.rgba(1, 1, 1, 0.72)
    }

    scale: chipMa.pressed ? 0.88 : 1.0
    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutBack } }

    property bool _fired: false

    Timer {
        id: longPressTimer
        interval: 700
        repeat:   false
        onTriggered: {
            chip._fired = true
            chip.longPress(chip.chipIndex)
        }
    }

    MouseArea {
        id:          chipMa
        anchors.fill: parent
        cursorShape:  Qt.PointingHandCursor
        onPressed:   { chip._fired = false; longPressTimer.start() }
        onReleased:  { longPressTimer.stop(); if (!chip._fired) chip.tapped(chip.chipIndex) }
        onCanceled:  longPressTimer.stop()
    }
}
