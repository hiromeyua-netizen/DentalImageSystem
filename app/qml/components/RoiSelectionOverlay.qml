import QtQuick

// ROI draw overlay: dim preview and drag a box to apply ROI.
Item {
    id: root
    anchors.fill: parent

    property bool roiMode: false
    signal roiCommitted(real x0n, real y0n, real x1n, real y1n)

    visible: roiMode
    enabled: roiMode

    property bool selecting: false
    property real sx: 0
    property real sy: 0
    property real ex: 0
    property real ey: 0

    readonly property real leftX: Math.min(sx, ex)
    readonly property real rightX: Math.max(sx, ex)
    readonly property real topY: Math.min(sy, ey)
    readonly property real bottomY: Math.max(sy, ey)
    readonly property real boxW: Math.max(0, rightX - leftX)
    readonly property real boxH: Math.max(0, bottomY - topY)

    // Base dim so ROI mode is immediately obvious when toggled on.
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, root.selecting ? 0.16 : 0.26)
    }

    Rectangle { // Top dim cut-out helper
        visible: root.selecting
        x: 0
        y: 0
        width: parent.width
        height: root.topY
        color: Qt.rgba(0, 0, 0, 0.32)
    }
    Rectangle { // Bottom dim
        visible: root.selecting
        x: 0
        y: root.bottomY
        width: parent.width
        height: Math.max(0, parent.height - root.bottomY)
        color: Qt.rgba(0, 0, 0, 0.32)
    }
    Rectangle { // Left dim
        visible: root.selecting
        x: 0
        y: root.topY
        width: root.leftX
        height: root.boxH
        color: Qt.rgba(0, 0, 0, 0.32)
    }
    Rectangle { // Right dim
        visible: root.selecting
        x: root.rightX
        y: root.topY
        width: Math.max(0, parent.width - root.rightX)
        height: root.boxH
        color: Qt.rgba(0, 0, 0, 0.32)
    }

    Rectangle { // Selection box
        visible: root.selecting
        x: root.leftX
        y: root.topY
        width: root.boxW
        height: root.boxH
        color: "transparent"
        border.width: 2
        border.color: Qt.rgba(1, 1, 1, 0.90)
        radius: 4
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 14
        visible: !root.selecting
        text: "ROI mode: drag diagonally to select area"
        font.pixelSize: 15
        font.bold: true
        color: Qt.rgba(1, 1, 1, 0.93)
        style: Text.Outline
        styleColor: Qt.rgba(0, 0, 0, 0.70)
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        cursorShape: root.selecting ? Qt.CrossCursor : Qt.CrossCursor

        onPressed: function (mouse) {
            root.selecting = true
            root.sx = mouse.x
            root.sy = mouse.y
            root.ex = mouse.x
            root.ey = mouse.y
        }

        onPositionChanged: function (mouse) {
            if (!root.selecting)
                return
            root.ex = Math.max(0, Math.min(width, mouse.x))
            root.ey = Math.max(0, Math.min(height, mouse.y))
        }

        onReleased: function (mouse) {
            if (!root.selecting)
                return
            root.ex = Math.max(0, Math.min(width, mouse.x))
            root.ey = Math.max(0, Math.min(height, mouse.y))
            root.selecting = false
            if (width <= 0 || height <= 0)
                return
            var x0n = root.sx / width
            var y0n = root.sy / height
            var x1n = root.ex / width
            var y1n = root.ey / height
            root.roiCommitted(x0n, y0n, x1n, y1n)
        }

        onCanceled: {
            root.selecting = false
        }
    }
}

