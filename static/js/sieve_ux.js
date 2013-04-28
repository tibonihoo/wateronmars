// sieve_ux.js Copyright 2013 Thibauld Nion - BSD licensed
// Requires jquery and mousetrap.js.
//
// Usage:
// Call prepareKeyBindings() in the head of the page.
// Call activateKeyBindings() at the end of the page.


// Preparation (mostly to set up some global variables)
function prepareKeyBindings()
{
  // keybindings globals
  gMouseTrapDisabled = true;
  gCurrentlyExpandedItem = -1;
  gNumReferences = 0;
}

// Activation that needs to be called once the page is fully generated
function activateKeyBindings()
{
  // keybindings globals
  gCurrentlyExpandedItem = -1;
  gMouseTrapDisabled = false;   
  gNumReferences = $(".reference").length;
  // hook the hide/show calbacks in the feed items
  for(idx=0;idx<gNumReferences;idx+=1)
  {
    currentId = 'collapse'+idx.toString()
    $("#"+currentId).on('hiden', createHiddenCallbackFunc(idx));
    $("#"+currentId).on('shown', createShownCallbackFunc(idx));
  }
}

// Make sure that an element is visible by scrolling the page if necessary to make it appear in the first 3 quarters of the page.
// adapted from http://stackoverflow.com/questions/487073/check-if-element-is-visible-after-scrolling 
function ensureVisibilityInFirstThreeQuarters(elem)
{
  var windowHeight = $(window).height();
  var windowTop = $(window).scrollTop();
  var docView4thTop = windowTop + windowHeight/4;
  var docView4thBottom = windowTop + ((2*windowHeight)/3);
  var elemTop = $(elem).offset().top;
  if (elemTop <= docView4thTop)
  {
    $('body,html').animate({scrollTop: elemTop-windowHeight/4}, 400); 
  }
  else if (elemTop >= docView4thBottom)
  {
    $('body,html').animate({scrollTop: elemTop-windowHeight/3}, 400); 
  }
}


// adapted from http://stackoverflow.com/questions/750486/javascript-closure-inside-loops-simple-practical-example
function createHiddenCallbackFunc(i) {
  return function() { 
    if (!gMouseTrapDisabled) 
    {
      gCurrentlyExpandedItem = -1;
    }  
  };
}

function createShownCallbackFunc(i) {
  return function() { 
    if (!gMouseTrapDisabled) 
    {
      gCurrentlyExpandedItem = i;
    }
    else
    {
      gMouseTrapDisabled = false;
    }
    ensureVisibilityInFirstThreeQuarters("#collapse"+i.toString());
  }
}


// Expand previous item
Mousetrap.bind('p', function() { 
  if(gMouseTrapDisabled) {return false;}
  gMouseTrapDisabled = true;
  var currentIdx = gCurrentlyExpandedItem;
  var itemToCollapse = 'collapse'+currentIdx.toString();
  $('#'+itemToCollapse).collapse('hide');
  var referenceId = '#reference'+currentIdx.toString()
  if ( !$(referenceId).hasClass('read') ) { $(referenceId).addClass("read") }; 
  if (gCurrentlyExpandedItem <= 0)
  {
    if (gCurrentlyExpandedItem == 0) { gCurrentlyExpandedItem = -1;}
    gMouseTrapDisabled = false;
  }
  else
  {
    var itemToExpand = 'collapse'+(currentIdx-1).toString();
    $('#'+itemToExpand).collapse('show');
    gCurrentlyExpandedItem = currentIdx - 1;
  }
});

// Expand next item
Mousetrap.bind('n', function() { 
  if(gMouseTrapDisabled) {return false;}
  gMouseTrapDisabled = true;
  var currentIdx = gCurrentlyExpandedItem;
  var itemToCollapse = 'collapse'+currentIdx.toString();
  $('#'+itemToCollapse).collapse('hide');
  var referenceId = '#reference'+currentIdx.toString()
  if ( !$(referenceId).hasClass('read') ) { $(referenceId).addClass("read") }; 
  if (gCurrentlyExpandedItem >= gNumReferences - 1)
  {
    if (gCurrentlyExpandedItem == gNumReferences - 1) { gCurrentlyExpandedItem = gNumReferences }
    gMouseTrapDisabled = false;
  }
  else
  {
    var itemToExpand = 'collapse'+(currentIdx+1).toString();
    $('#'+itemToExpand).collapse('show');
    gCurrentlyExpandedItem = currentIdx + 1;
  }
});

// open the currently expanded items' linked page in the browser
Mousetrap.bind('v', function() { 
  var currentIdx = gCurrentlyExpandedItem;
  var itemToShow = '#referenceUrl'+currentIdx.toString();
  window.open($(itemToShow).prop("href"));
});
