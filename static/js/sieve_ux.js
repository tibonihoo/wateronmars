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
  gSyncWithServer = false;
  gReadURLs = [];
}


// Activation that needs to be called once the page is fully generated
// @param syncWithServer a boolean telling whether the read status
// should be synced with the server.
function activateKeyBindings(syncWithServer)
{
  // keybindings globals
  gCurrentlyExpandedItem = -1;
  gMouseTrapDisabled = false;   
  gNumReferences = $(".reference").length;
  gSyncWithServer = syncWithServer;
  // hook the hide/show calbacks in the feed items
  for(idx=0;idx<gNumReferences;idx+=1)
  {
    currentId = 'collapse'+idx.toString()
    $("#"+currentId).on('hiden', createHiddenCallbackFunc(idx));
    $("#"+currentId).on('shown', createShownCallbackFunc(idx));
  }
}

// Show one of the warning that are written but hidden by default on
// the page, and that are identified via their HTML id.
// WARNING: if there are several warnings, they may overlap (TODO: in
// such case use a warning counter + a shift computed accordingly)
function showWarning(warningId) {
  var warningElt = $("#"+warningId);
  warningElt.popover();
  warningElt.css({ 
    "display": "block",
    "position": "absolute",
    "left": "3px",
    "top": $(window).height()/3.});
}

// Hide a specific warning.
function hideWarning(warningId) {
  $("#"+warningId).css("display", "none");
}

// Make sure that an element is visible by scrolling the page if necessary to make it appear in the first 3 quarters of the page.
// Note: adapted from http://stackoverflow.com/questions/487073/check-if-element-is-visible-after-scrolling 
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

// Generate the callback that will be called when the content of
// reference#i will be collapsed.
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


// Generate the callback that will be called when the content of
// reference#i will be collapsed.
// Note: adapted from http://stackoverflow.com/questions/750486/javascript-closure-inside-loops-simple-practical-example
function createHiddenCallbackFunc(i) {
  return function() { 
    if (!gMouseTrapDisabled) 
    {
      gCurrentlyExpandedItem = -1;
    }  
  };
}

// using jQuery to get a cookie 
// (from https://docs.djangoproject.com/en/dev/ref/contrib/csrf/)
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Django-specific method to distinguish which request needs to take
// care of the crsf protection
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// Make sure the server will know that certain items have been read
// @param read_items_urls a list of urls identifying the references
// that must be considered as read.
// @param callback function to be called when the server's answer is received
function updateReadStatusOnServer(read_items_urls, callback) {
  if (!gSyncWithServer) return;
  var jsonStr = JSON.stringify({"action": "read","references":read_items_urls})
  var csrftoken = getCookie('csrftoken');
  var currentURL = window.location.href;
  $.ajax({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
      if (!csrfSafeMethod(settings.type)) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
    },
    type: "POST",
    url: currentURL,
    data: jsonStr,
    dataType: "json",
  }).done(callback).fail(function () {showWarning("server-sync-problem");});
  // }).done(callback).fail(function(j,t) {alert(t);} );
}



// Perform all necessary stuff to indicate that a reference should be
// considered as read.
// Note: will act only if the reference has not be marked as read yet !
// @param refElement the element representing the reference that must
// be marked as read
// @param refIdx the index of this reference (typically as indicated
// in #reference{refIdx)
function markAsRead(refElement,refIdx) {
  if ( !refElement.hasClass('read') ) { 
    refElement.addClass("read") 
    gReadURLs.push($('#referenceUrl'+refIdx.toString()).prop("href"));
    // we still upload the full *current* list of read items (if
    // there's more than one it probably means that something went
    // wrong with the latest update)
    updateReadStatusOnServer(gReadURLs,function (data) {gReadURLs = []; hideWarning("server-sync-problem");});
  };
}


// Keybinding activation

// Expand previous item
Mousetrap.bind('p', function() { 
  if(gMouseTrapDisabled) {return false;}
  gMouseTrapDisabled = true;
  var currentIdx = gCurrentlyExpandedItem;
  var itemToCollapse = 'collapse'+currentIdx.toString();
  $('#'+itemToCollapse).collapse('hide');
  var referenceId = '#reference'+currentIdx.toString()
  markAsRead($(referenceId),currentIdx);
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
  if ( currentIdx>-1 ) 
  { 
    markAsRead($(referenceId),currentIdx);
  }
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

// open the currently expanded items' linked page in the browser
Mousetrap.bind('r', function() { 
  var window_location = window.location;
  updateReadStatusOnServer(gReadURLs,function (data) {gReadURLs = []; window_location.reload();});
  // TODO apparently there is a need for a little timeout to get a
  // coherent refresh of the page !
});
