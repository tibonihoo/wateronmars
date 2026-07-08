// sieve_ux.js
// Copyright (C) 2013-2026 Thibauld Nion
//
// This file is part of WaterOnMars (https://github.com/tibonihoo/wateronmars).
//
// WaterOnMars is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// WaterOnMars is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with WaterOnMars.  If not, see <http://www.gnu.org/licenses/>.
//
//
// Requirements:
// - mousetrap.js v1.1.3
// - wom_base.js
//
// Usage:
// Call prepareKeyBindings() in the head of the page.
// Call activateKeyBindings() at the end of the page.


// Preparation (mostly to set up some global variables)
function prepareKeyBindings()
{
  // keybindings globals
  gMouseTrapDisabled = true;
  gCurrentlyFocusedItem = -1;
  gNumReferences = 0;
  gSyncWithServer = false;
  gWaitingForServerAnswer = false;
  gReadURLs = [];
  gUserCollectionURL = "";
  gNumUnread = 0;
  gInitialNumUnread = 0;
  gCarousel = null;
  gSmallWindowWidthThreshold = 800;
}

function getFirstVisible(selector)
{
  const allMatches = document.querySelectorAll(selector);
  for (var i = 0; i < allMatches.length; i++)
  {
    let currentElement = allMatches[i];
    let computedStyle = window.getComputedStyle(currentElement);
    let isHidden = ((computedStyle.display === 'none') || (computedStyle.visibility === 'hidden'))
    if (!isHidden)
      return currentElement;
  }
}

// Make sure that the item being slid out is marked as read and that
// the next item and its title are displayed correctly.
function onCarouselSlid(event)
{
  // get the index by slicing the "wom-refXXX" id after a len(wom-ref) offset
  newlyShownItemIndex = event.to;
  previouslyShownItemIndex = event.from;

  if (previouslyShownItemIndex >= 0 && previouslyShownItemIndex <= gNumReferences - 1)
  {
    var referenceId = '#wom-ref'+previouslyShownItemIndex.toString();
    var prevNavItem = "#wom-ref-nav-"+previouslyShownItemIndex.toString();
    $(prevNavItem).classList.remove("shown");
    markAsRead($(referenceId), previouslyShownItemIndex);
  }

  if (newlyShownItemIndex >= 0 && newlyShownItemIndex <= gNumReferences - 1)
  {
    var navItem = "#wom-ref-nav-" + newlyShownItemIndex.toString();
    $(navItem).classList.add("shown");
    ensureCorrectVisibility(navItem,"#wom-title-list");
  }

  gCurrentlyFocusedItem  = newlyShownItemIndex;
  adaptControlsDisplay();

  if (window.innerWidth < gSmallWindowWidthThreshold)
      hideTitleList();

}

// Ensure controls are visible only when they make sense
function adaptControlsDisplay() {
  if (gNumReferences==0)
  {
    $(".carousel-control-prev").style.display = 'none';
    $(".carousel-control-next").style.display= 'none';
    return;
  }

  if(gCurrentlyFocusedItem > 0) {
    $(".carousel-control-prev").style.display = 'block';
  }
  else {
    $(".carousel-control-prev").style.display = 'none';
  }

  if(gCurrentlyFocusedItem < gNumReferences) {
    $(".carousel-control-next").style.display = 'block';
  }
  else {
    $(".carousel-control-next").style.display = 'none';
  }

  let newlyShownItemId = getFirstVisible(".carousel-item").getAttribute("id");
  $("#"+newlyShownItemId).focus();

}

// Initialize the carousel, activate its controls and plug the right callbacks.
function initializeCarousel()
{
  const myCarouselElement = document.querySelector('#wom-sieve-frame');
  gCarousel = new bootstrap.Carousel(myCarouselElement, {
      keyboard: true,
      touch: true,
      wrap: false
  });
  gCurrentlyFocusedItem = 0;
  adaptControlsDisplay();
  // add event
  $(".carousel").addEventListener('slid.bs.carousel',  function (event) { onCarouselSlid(event); });
  showWarning("wom-sieve-demo-warning");
}

function switchTitleListDisplay()
{
  if ($(".wom-title-list-switch.active"))
    hideTitleList();
  else
    showTitleList();
}


function hideTitleList()
{
  $("#wom-title-list-container").classList.remove("col-md-2");
  $(".carousel").classList.remove("col-md-10");
  $("#wom-title-list-container").hidden = true;
  $(".carousel").classList.add("col-md-12");
  $(".wom-title-list-switch").classList.remove("active");
}

function showTitleList()
{
  $("#wom-title-list-container").hidden = false;
  $(".carousel").classList.remove("col-md-12");
  $("#wom-title-list-container").classList.add("col-md-2");
  $(".carousel").classList.add("col-md-10");
  $(".wom-title-list-switch").classList.add("active");
}


// Activation that needs to be called once the page is fully generated
// @param syncWithServer a boolean telling whether the read status
// @param userCollectionURL the url to which new bookmarks should be posted
// @param numUnread the total number of unread items (currently ignored)
// should be synced with the server.
function activateKeyBindings(syncWithServer,userCollectionURL,numUnread)
{
  // keybindings globals
  gCurrentlyFocusedItem = -1;
  gMouseTrapDisabled = false;
  gNumReferences = document.querySelectorAll(".wom-reference").length;
  gSyncWithServer = syncWithServer;
  gUserCollectionURL = userCollectionURL;
  // only count the numbe of unread items directly accessible by the
  // user (anything else feels weirder)
  gNumUnread = gNumReferences;
  gInitialNumUnread = gNumUnread;
  $("#wom-sieve-reload").addEventListener('click',function (){reloadSieve();});
  initializeCarousel();
  // Move the title list away in two cases:
  // - when the screen space is scarse
  // - when there are no news at all
  if (window.innerWidth < gSmallWindowWidthThreshold || gInitialNumUnread<=1)
    hideTitleList();
  else
    showTitleList();
}



// Make sure that an element (in the title list) is visible by scrolling
// the page if necessary to make it appear at a comfortable place on the page.
// Note: adapted from http://stackoverflow.com/questions/487073/check-if-element-is-visible-after-scrolling
function ensureCorrectVisibility(elem, container)
{
  let containerElement = $(container)
  let containerComputedStyle = window.getComputedStyle(containerElement);
  let isHidden = ((containerComputedStyle.display === 'none') || (containerComputedStyle.visibility === 'hidden'))
  if (! isHidden) {
    let containerBoundingRect = containerElement.getBoundingClientRect();
    let containerHeight = containerBoundingRect.height;
    let containerTop = containerBoundingRect.top;
    let visibilityTopThreshold = containerHeight/4;
    let visibilityBottomThreshold = containerHeight/2;
    let elementBoundingRect = $(elem).getBoundingClientRect();
    let elementRelativeTop = elementBoundingRect.top - containerTop;
    if ( (elementRelativeTop <= visibilityTopThreshold) || (elementRelativeTop >= visibilityBottomThreshold) )
    {
      let scrollNewTop = elementRelativeTop-visibilityTopThreshold; //+containerTop;
      containerElement.scrollBy({
          top: scrollNewTop,
          behaviour: "smooth"
      });
    }
  }
}



// Make sure the server will know that certain items have been read
// @param read_items_urls a list of urls identifying the references
// that must be considered as read.
// @param callback function to be called when the server's answer is received
function updateReadStatusOnServer(read_items_urls)
{
  if (!gSyncWithServer) return;
  var jsonStr = JSON.stringify({"action": "read","references":read_items_urls})
  var currentURL = window.location.href;
  return womRequest("POST", currentURL, "application/json", jsonStr);
}


// Send a reference's info to add it to the user's collection
// @param url reference's URL
// @param title reference's title
// @param sourceURL URL of the reference's source
// @param sourceTitle name of the reference's source
// @param callback function to be called when the server's answer is received
function saveBookmarkOnServer (url,title,sourceURL,sourceTitle,callback)
{
  if (gUserCollectionURL=="") return;
  var jsonStr = JSON.stringify({"url": url, "title" : title, "source_url" : sourceURL, "source_title" : sourceTitle });
  womRequest("POST", gUserCollectionURL, "application/json", jsonStr)
    .then(callback)
    .catch(function () {showWarning("wom-server-save-failed");});
}

function updateReadingProgress()
{
  progress = Math.round(100*(gInitialNumUnread-gNumUnread)/gInitialNumUnread);
  elt = $("#wom-sieve-reading-progress .progress-bar")
  elt.setAttribute("aria-valuenow",progress.toString());
  elt.style.width = ""+progress.toString()+"%";
}


// Perform all necessary stuff to indicate that a reference should be
// considered as read.
// Note: will act only if the reference has not be marked as read yet !
// @param refElement the element representing the reference that must
// be marked as read
// @param refIdx the index of this reference (typically as indicated
// in #wom-ref{refIdx}
function markAsRead(refElement,refIdx) {
  if ( gNumReferences>0 && !refElement.classList.contains('read') ) {
    refElement.classList.add("read");
    $("#wom-ref-nav-"+refIdx.toString()).classList.add('read');
    url_elt = document.getElementById('wom-ref'+refIdx.toString()+"-url");
    // NOTE: calling .href on the element proved to apply a silent encoding (at least on firefox)
    // whereas getAttributes provided an untouched value
    raw_url = url_elt.getAttribute("href")
    gReadURLs.push(raw_url);
    rollingUpdateReadStatusOnServer(true);
    gNumUnread -= 1;
    updateReadingProgress();
  }
}

// Make sure to synchronize the read status of update on the server.
// Will continue to update the status if when the server answers, new
// items have been read.
function rollingUpdateReadStatusOnServer(check_lock) {
  if (!check_lock || !gWaitingForServerAnswer) {
    gWaitingForServerAnswer = true;
    var syncedReadURLS = gReadURLs.slice(0)
    gReadURLs = [];
    // we still upload the full *current* list of read items (if
    // there's more than one it probably means that something went
    // wrong with the latest update)
    updateReadStatusOnServer(syncedReadURLS)
    .then(function (response) {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      hideWarning("wom-server-sync-problem");
      if (gReadURLs.length>0) {rollingUpdateReadStatusOnServer(false)}
      else {gWaitingForServerAnswer=false;} })
    .catch(function () {
      showWarning("wom-server-sync-problem");
      gWaitingForServerAnswer=false;});
  }
}

// Make sure that the user gets a visual feedback indicating that the
// reference has been saved.
// @param refIdx the index of this reference (typically as indicated
// in #wom-ref{refIdx}
function markAsSaved(refIdx) {
  var refIdxStr = refIdx.toString();
  var refElement = $('#wom-ref'+refIdxStr);
  if ( !refElement.classList.contains('saved') ) {
    var url = document.getElementById('wom-ref'+refIdxStr+'-url').href;
    var title = document.getElementById('wom-ref'+refIdxStr+'-url').title;
    var sourceURL = document.getElementById('wom-ref'+refIdxStr+'-source-url').href;
    var sourceTitle = document.getElementById('wom-ref'+refIdxStr+'-source-url').title;
    saveBookmarkOnServer(url,title,sourceURL,sourceTitle, function(data) {refElement.classList.add("saved");});
  };
}


// Keybinding activation

// Show previous item
Mousetrap.bind('p', function() {
  if(gMouseTrapDisabled) {return false;}
  gMouseTrapDisabled = true;
  if (gCurrentlyFocusedItem > 0)
  {
    gCarousel.prev();
  }
  gMouseTrapDisabled = false;
});


// Show next item
Mousetrap.bind('n', function() {
  if(gMouseTrapDisabled) {return false;}
  gMouseTrapDisabled = true;
  if (gCurrentlyFocusedItem < gNumReferences)
  {
    gCarousel.next();
  }
  gMouseTrapDisabled = false;
});

// open the currently expanded items' linked page in the browser
Mousetrap.bind('v', function() {
  var itemToShow = 'wom-ref'+gCurrentlyFocusedItem.toString()+"-url";
  window.open(document.getElementById(itemToShow).href);
});

// Reload the sieve but also makes sure to sync the read state of news
// items on the server before quitting page.
function reloadSieve()
{
  var window_location = window.location;
  if (gReadURLs.length>0) {
    showWarning("wom-sieve-news-loading");
    updateReadStatusOnServer(gReadURLs)
    .then(function (data) {gReadURLs = []; window_location.reload();});
  }
  else {
    window_location.reload();
  }
}
Mousetrap.bind('r', reloadSieve);


// save the ref corresponding to the currently expanded items
function saveCurrentItem() {
  markAsSaved(gCurrentlyFocusedItem);
}
Mousetrap.bind('b', saveCurrentItem);


Mousetrap.bind('h', switchTitleListDisplay);
