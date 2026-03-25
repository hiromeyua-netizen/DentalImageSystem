import QtQuick

// Interactive ROI overlay drawn on top of the camera image area.
// When visible (roiModeActive), the user can draw/move a selection rectangle.
Item {
    id: root

    // Reported dimensions of the actual painted camera image (in local coords)
    property real imageW: width
    property real imageH: height
    property real imageX: 0
    property real imageY: 0

    // Current ROI in normalised image coordinates (0–1)
    property real roiNX: 0.25
    property real roiNY: 0.25
    property real roiNW: 0.50
    property real roiNH: 0.50

    // Convert normalised → pixel (within this Item)
    readonly property real _px: imageX + roiNX * imageW
    readonly property real _py: imageY + roiNY * imageH
    readonly property real _pw: roiNW * imageW
    readonly property real _ph: roiNH * imageH

    // Drag state
    property bool   _drawing: false
    property real   _dragStartX: 0
    property real   _dragStartY: 0

    // Semi-transparent overlay outside ROI
    Rectangle {
        id: overlay
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.35)

        // Punch a hole (transparent) where the ROI is using a Canvas
        Canvas {
            id: roiCanvas
            anchors.fill: parent
            renderTarget: Canvas.Image
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "rgba(0,0,0,0.38)"
                ctx.fillRect(0, 0, width, height)
                ctx.clearRect(root._px, root._py, root._pw, root._ph)
            }

            Connections {
                target: root
                function onRoiNXChanged() { roiCanvas.requestPaint() }
                function onRoiNYChanged() { roiCanvas.requestPaint() }
                function onRoiNWChanged() { roiCanvas.requestPaint() }
                function onRoiNHChanged() { roiCanvas.requestPaint() }
            }
        }
    }

    // ROI border rectangle
    Rectangle {
        x: root._px; y: root._py; width: root._pw; height: root._ph
        color: "transparent"
        border.color: "#00e676"
        border.width: 2
        radius: 3

        // Corner handles
        Repeater {
            model: 4
            Rectangle {
                property int cx: [0,1,1,0][index]
                property int cy: [0,0,1,1][index]
                x: cx * (parent.width  - width)
                y: cy * (parent.height - height)
                width: 12; height: 12; radius: 2
                color: "#00e676"
            }
        }

            // Label
            Rectangle {
                anchors { top: parent.top; left: parent.left; margins: -1 }
                color: "#00e676"; radius: 3
                width: roiLbl.implicitWidth + 6; height: roiLbl.implicitHeight + 4
                Text { id: roiLbl; anchors.centerIn: parent; text: "ROI"; color: "#000"; font.pixelSize: 10; font.bold: true; font.family: "Segoe UI" }
            }
    }

    // Mouse area for drawing/moving
    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.CrossCursor
        onPressed: function(mouse) {
            var nx = (mouse.x - root.imageX) / root.imageW
            var ny = (mouse.y - root.imageY) / root.imageH
            root._dragStartX = nx
            root._dragStartY = ny
            root._drawing = true
        }
        onPositionChanged: function(mouse) {
            if (!root._drawing) return
            var nx = Math.max(0, Math.min(1, (mouse.x - root.imageX) / root.imageW))
            var ny = Math.max(0, Math.min(1, (mouse.y - root.imageY) / root.imageH))
            root.roiNX = Math.min(root._dragStartX, nx)
            root.roiNY = Math.min(root._dragStartY, ny)
            root.roiNW = Math.abs(nx - root._dragStartX)
            root.roiNH = Math.abs(ny - root._dragStartY)
        }
        onReleased: {
            root._drawing = false
            // Notify Python with normalised coords
            bridge.setROIFromNormalized(root.roiNX, root.roiNY, root.roiNW, root.roiNH)
        }
    }
}
