import QtQuick

// Rule-of-thirds grid + center crosshair for live preview (Settings toggles).
Item {
    id: root
    anchors.fill: parent

    property bool showOverlay: true
    property bool showGrid: false
    property bool showCrosshair: false

    visible: showOverlay && (showGrid || showCrosshair)

    Item {
        anchors.fill: parent
        visible: root.showGrid
        opacity: 0.92

        Repeater {
            model: [1 / 3, 2 / 3]
            delegate: Rectangle {
                required property real modelData
                x: Math.round(parent.width * modelData)
                y: 0
                width: 1
                height: parent.height
                color: Qt.rgba(1, 1, 1, 0.34)
            }
        }

        Repeater {
            model: [1 / 3, 2 / 3]
            delegate: Rectangle {
                required property real modelData
                x: 0
                y: Math.round(parent.height * modelData)
                width: parent.width
                height: 1
                color: Qt.rgba(1, 1, 1, 0.34)
            }
        }
    }

    Item {
        anchors.fill: parent
        visible: root.showCrosshair

        readonly property real cx: width * 0.5
        readonly property real cy: height * 0.5
        readonly property real gap: Math.max(9, Math.min(width, height) * 0.014)
        readonly property real arm: Math.max(14, Math.min(width, height) * 0.052)

        Rectangle {
            x: Math.round(parent.cx - parent.arm - parent.gap)
            y: Math.round(parent.cy)
            width: Math.round(parent.arm)
            height: 1
            color: Qt.rgba(1, 1, 1, 0.88)
        }
        Rectangle {
            x: Math.round(parent.cx + parent.gap)
            y: Math.round(parent.cy)
            width: Math.round(parent.arm)
            height: 1
            color: Qt.rgba(1, 1, 1, 0.88)
        }
        Rectangle {
            x: Math.round(parent.cx)
            y: Math.round(parent.cy - parent.arm - parent.gap)
            width: 1
            height: Math.round(parent.arm)
            color: Qt.rgba(1, 1, 1, 0.88)
        }
        Rectangle {
            x: Math.round(parent.cx)
            y: Math.round(parent.cy + parent.gap)
            width: 1
            height: Math.round(parent.arm)
            color: Qt.rgba(1, 1, 1, 0.88)
        }

        Rectangle {
            x: Math.round(parent.cx - 4)
            y: Math.round(parent.cy - 4)
            width: 8
            height: 8
            radius: 4
            color: "transparent"
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.88)
        }
    }
}
