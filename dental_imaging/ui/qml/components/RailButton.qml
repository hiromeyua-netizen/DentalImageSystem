import QtQuick
import QtQuick.Controls

// Icon-only tool button for the right rail.
// Properties:
//   iconSource  url   — path to SVG icon
//   tooltip     string
//   isChecked   bool  — managed externally (we don't use AbstractButton.checked
//                       so the Python bridge stays the single source of truth)
AbstractButton {
    id: root

    property url   iconSource
    property alias tooltip:    tip.text
    property bool  isChecked:  false

    // Override per-button for green/blue active tints
    property color activeColor:   Qt.rgba(1, 1, 1, 0.18)
    property color checkedBorder: Qt.rgba(1, 1, 1, 0.35)

    implicitWidth:  54
    implicitHeight: 54

    // Background capsule
    background: Rectangle {
        radius: 10
        color: {
            if (root.isChecked)                        return root.activeColor
            if (root.pressed || root.hovered) return Qt.rgba(1, 1, 1, 0.12)
            return "transparent"
        }
        border.width: root.isChecked ? 1 : 0
        border.color: root.isChecked ? root.checkedBorder : "transparent"

        Behavior on color        { ColorAnimation { duration: 120 } }
        Behavior on border.color { ColorAnimation { duration: 120 } }
    }

    // SVG icon — Qt renders SVG currentColor as black; we invert via opacity tinting
    contentItem: Image {
        anchors.centerIn: parent
        source:           root.iconSource
        sourceSize:       Qt.size(26, 26)
        fillMode:         Image.PreserveAspectFit
        opacity:          root.isChecked ? 1.0 : (root.hovered ? 0.95 : 0.72)
        Behavior on opacity { NumberAnimation { duration: 100 } }
    }

    // Press shrink feedback
    scale: root.pressed ? 0.88 : 1.0
    Behavior on scale { NumberAnimation { duration: 80; easing.type: Easing.OutBack } }

    ToolTip {
        id:      tip
        visible: root.hovered && text.length > 0
        delay:   600
        timeout: 3000
        font.pixelSize: 12
    }
}
