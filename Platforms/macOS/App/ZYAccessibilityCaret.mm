#import "ZYAccessibilityCaret.h"
#import <ApplicationServices/ApplicationServices.h>
#include <math.h>

static BOOL accessibilityTrusted(void){
    if(AXIsProcessTrusted()) return YES;
    static BOOL asked=NO;
    if(!asked){
        asked=YES;
        AXIsProcessTrustedWithOptions((__bridge CFDictionaryRef)@{(__bridge NSString *)kAXTrustedCheckOptionPrompt:@YES});
    }
    return NO;
}

static BOOL usableAXCaretBounds(CGRect bounds){
    // Insertion-point bounds are commonly zero-width. CGRectIsEmpty would reject them.
    return !CGRectIsNull(bounds) && !CGRectIsInfinite(bounds) &&
           isfinite(bounds.origin.x) && isfinite(bounds.origin.y) &&
           isfinite(bounds.size.width) && isfinite(bounds.size.height) &&
           bounds.size.width >= 0.0 && bounds.size.height > 0.0;
}

static NSRect queryAccessibilityCaretRect(void){
    if(!accessibilityTrusted()) return NSZeroRect;
    AXUIElementRef system=AXUIElementCreateSystemWide(),focused=NULL;
    CFTypeRef rangeValue=NULL,boundsValue=NULL;
    CFRange range={0,0}; CGRect bounds=CGRectZero; NSRect result=NSZeroRect;
    CGPoint anchor=CGPointZero;
    if(!system || AXUIElementCopyAttributeValue(system,kAXFocusedUIElementAttribute,(CFTypeRef *)&focused)!=kAXErrorSuccess || !focused) goto done;
    if(AXUIElementCopyAttributeValue(focused,kAXSelectedTextRangeAttribute,&rangeValue)!=kAXErrorSuccess ||
       !rangeValue || CFGetTypeID(rangeValue)!=AXValueGetTypeID() ||
       !AXValueGetValue((AXValueRef)rangeValue,(AXValueType)kAXValueCFRangeType,&range)) goto done;
    if(AXUIElementCopyParameterizedAttributeValue(focused,kAXBoundsForRangeParameterizedAttribute,rangeValue,&boundsValue)!=kAXErrorSuccess ||
       !boundsValue || CFGetTypeID(boundsValue)!=AXValueGetTypeID() ||
       !AXValueGetValue((AXValueRef)boundsValue,(AXValueType)kAXValueCGRectType,&bounds) || !usableAXCaretBounds(bounds)) goto done;

    // Quartz accessibility coordinates are display coordinates. Pick a display by the caret anchor
    // point rather than rectangle intersection so a zero-width insertion caret remains valid.
    anchor=CGPointMake(CGRectGetMinX(bounds),CGRectGetMidY(bounds));
    for(NSScreen *screen in NSScreen.screens){
        CGDirectDisplayID display=[screen.deviceDescription[@"NSScreenNumber"] unsignedIntValue];
        CGRect displayBounds=CGDisplayBounds(display);
        if(!CGRectContainsPoint(displayBounds,anchor)) continue;
        NSRect frame=screen.frame;
        result=NSMakeRect(NSMinX(frame)+CGRectGetMinX(bounds)-CGRectGetMinX(displayBounds),
                          NSMaxY(frame)-(CGRectGetMaxY(bounds)-CGRectGetMinY(displayBounds)),
                          CGRectGetWidth(bounds),CGRectGetHeight(bounds));
        break;
    }
done:
    if(boundsValue) CFRelease(boundsValue);
    if(rangeValue) CFRelease(rangeValue);
    if(focused) CFRelease(focused);
    if(system) CFRelease(system);
    return result;
}

NSRect ZYAccessibilityCaretRect(void){ return queryAccessibilityCaretRect(); }
