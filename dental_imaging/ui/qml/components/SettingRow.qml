import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

// A label + slider + percent value row for the image settings panel.
RowLayout {
    id: row

    property string label: ""
    property int    value: 50

    signal moved(int v)

    spacing: 10
    Layout.fillWidth: true

    Text {
        text:                label
        font.pixelSize:      11
        color:               "#b0b0be"
        Layout.preferredWidth: 100
    }

    Slider {
        id:          sl
        Layout.fillWidth: true
        from:        0
        to:          100
        value:       row.value
        stepSize:    1

        background: Rectangle {
            x:      sl.leftPadding
            y:      sl.topPadding + (sl.availableHeight - height) / 2
            width:  sl.availableWidth
            height: 4
            radius: 2
            color:  Qt.rgba(1, 1, 1, 0.15)

            Rectangle {
                width:  sl.visualPosition * parent.width
                height: parent.height
                radius: 2
                color:  Qt.rgba(1, 1, 1, 0.55)
            }
        }

        handle: Rectangle {
            x:      sl.leftPadding + sl.visualPosition * (sl.availableWidth - width)
            y:      sl.topPadding + (sl.availableHeight - height) / 2
            width:  18
            height: 18
            radius: 9
            color:  "white"
        }

        onMoved: row.moved(Math.round(sl.value))
    }

    Text {
        text:                sl.value.toFixed(0) + "%"
        font.pixelSize:      11
        color:               "#d0d0dc"
        Layout.preferredWidth: 36
        horizontalAlignment: Text.AlignRight
    }
}
