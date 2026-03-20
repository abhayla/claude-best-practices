# Engagement Actions

### Engagement Actions

| Action | Method | Endpoint | Body |
|--------|--------|----------|------|
| Upvote | POST | `/api/vote` | `id=THING_ID&dir=1` |
| Downvote | POST | `/api/vote` | `id=THING_ID&dir=-1` |
| Unvote | POST | `/api/vote` | `id=THING_ID&dir=0` |
| Save | POST | `/api/save` | `id=THING_ID` |
| Unsave | POST | `/api/unsave` | `id=THING_ID` |
| Edit | POST | `/api/editusertext` | `thing_id=THING_ID&text=NEW_TEXT` |
| Delete | POST | `/api/del` | `id=THING_ID` |
| Hide | POST | `/api/hide` | `id=THING_ID` |
| Report | POST | `/api/report` | `thing_id=THING_ID&reason=REASON` |
| Crosspost | POST | `/api/submit` | `kind=crosspost&sr=TARGET_SR&crosspost_fullname=t3_POST_ID&title=TITLE` |

