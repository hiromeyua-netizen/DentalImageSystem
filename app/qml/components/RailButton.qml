import QtQuick
import QtQuick.Controls
import QtQuick.Window

// Icon-only button for the right tool rail.
// isChecked is set externally by the bridge — not a toggle inside the component.
AbstractButton {
    id: root

    property url   iconSource
    property alias tooltip:      tip.text
    property bool  isChecked:    false
    property color activeColor:  Qt.rgba(1, 1, 1, 0.15)
    property color activeBorder: Qt.rgba(1, 1, 1, 0.38)

    implicitWidth:  60
    implicitHeight: 60
    // Rail assigns a fixed column width; keep hit-target and highlight square (not wide × short).
    height: width

    background: Rectangle {
        radius: Math.min(width, height) * 0.22
        color: root.isChecked   ? root.activeColor          :
               root.pressed     ? Qt.rgba(1, 1, 1, 0.14)   :
               root.hovered     ? Qt.rgba(1, 1, 1, 0.08)   : "transparent"
        border.width: root.isChecked ? 1 : 0
        border.color: root.isChecked ? root.activeBorder : "transparent"
        Behavior on color        { ColorAnimation { duration: 120 } }
        Behavior on border.color { ColorAnimation { duration: 120 } }
    }

    contentItem: Image {
        anchors.centerIn: parent
        width:               22
        height:              22
        source:              root.iconSource
        // Rasterize SVG at ≥2× DPR — Qt at 22×22 looks soft / breaks thin arcs on HiDPI.
        readonly property real _dpr: Math.max(2, Screen.devicePixelRatio)
        sourceSize:          Qt.size(Math.ceil(22 * _dpr), Math.ceil(22 * _dpr))
        fillMode:            Image.PreserveAspectFit
        smooth:              true
        mipmap:              true
        opacity:             root.isChecked ? 1.0 : root.hovered ? 0.90 : 0.62
        Behavior on opacity { NumberAnimation { duration: 110 } }
    }

    scale: root.pressed ? 0.87 : 1.0
    Behavior on scale { NumberAnimation { duration: 80; easing.type: Easing.OutBack } }

    ToolTip { id: tip; visible: root.hovered && tip.text.length > 0; delay: 500 }
}
