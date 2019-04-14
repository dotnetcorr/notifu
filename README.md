# Noti-Fu
Telegram bot for notifications (ex-planned-part of Task-Fu)

## ToDo:
- [x] Handle all timestamps in UTC instead of local TZ
- [x] Show list of all notifications
- [x] Store notification data for restoring after restart
- [ ] Handle errors correctly, write to log
- [ ] Change markup of notification text for more readability
- [ ] Make start and help commands more useful
- [ ] (optional) Handle dictionary keys without setdefault (due to redundant constructor calls)
- [ ] Show timezones in every notification
- [x] Implement help command handling
- [ ] Implement notification removing logic
- [ ] (optional) Use buttons to manipulate timezones
- [ ] Handle periodic notifications
- [ ] Add more items to this list


## Notes
- Simple persistence implemented with pickles. Cases when notifu will be stored:
    * Creating a new notifu object
    * Changing a timezone
    * Adding a new notification
    * Removing notification
    * Executing notifications