import AppKit
let output=CommandLine.arguments[1]
try FileManager.default.createDirectory(atPath:output,withIntermediateDirectories:true)
for size in [16,32,128,256,512] { for multiplier in [1,2] {
 let pixels=size*multiplier,n=CGFloat(pixels)
 let bitmap=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:pixels,pixelsHigh:pixels,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
 NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(bitmapImageRep:bitmap)
 NSColor(calibratedRed:0.075,green:0.20,blue:0.18,alpha:1).setFill()
 NSBezierPath(roundedRect:NSRect(x:n*0.04,y:n*0.04,width:n*0.92,height:n*0.92),xRadius:n*0.2,yRadius:n*0.2).fill()
 let tr=AffineTransform(translationByX:n*0.12,byY:n*0.88);var transform=tr;transform.scale(x:n*0.0076,y:-n*0.0076)
 let p=NSBezierPath();p.move(to:NSPoint(x:17,y:23));p.curve(to:NSPoint(x:86,y:24),controlPoint1:NSPoint(x:30,y:9),controlPoint2:NSPoint(x:76,y:9));p.curve(to:NSPoint(x:26,y:31),controlPoint1:NSPoint(x:93,y:36),controlPoint2:NSPoint(x:42,y:40))
 p.move(to:NSPoint(x:24,y:45));p.curve(to:NSPoint(x:78,y:44),controlPoint1:NSPoint(x:38,y:51),controlPoint2:NSPoint(x:69,y:50))
 p.move(to:NSPoint(x:33,y:60));p.curve(to:NSPoint(x:67,y:58),controlPoint1:NSPoint(x:44,y:65),controlPoint2:NSPoint(x:61,y:63))
 p.move(to:NSPoint(x:42,y:75));p.curve(to:NSPoint(x:58,y:71),controlPoint1:NSPoint(x:49,y:78),controlPoint2:NSPoint(x:55,y:75));p.line(to:NSPoint(x:48,y:90));p.transform(using:transform);p.lineWidth=n*0.0532;p.lineCapStyle = .round
 NSColor(calibratedRed:0.88,green:0.74,blue:0.47,alpha:1).setStroke();p.stroke()
 let q=NSBezierPath();q.move(to:NSPoint(x:16,y:56));for point in [(34,44),(47,48),(67,28),(80,29)]{q.line(to:NSPoint(x:point.0,y:point.1))};q.transform(using:transform);q.lineWidth=n*0.038;q.lineCapStyle = .round;q.lineJoinStyle = .round;NSColor.white.setStroke();q.stroke()
 NSGraphicsContext.restoreGraphicsState()
 try bitmap.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:output).appendingPathComponent("icon_\(size)x\(size)\(multiplier==2 ? "@2x":"").png"))
}}
