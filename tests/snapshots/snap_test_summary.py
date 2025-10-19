# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_maybe_write_github_summaries[False] 1'] = '''
_PR/Issue summary_

[`repository-owner-0`](https://github.com/repository-owner-0)
- [`repository-name-0`](https://github.com/repository-owner-0/repository-name-0)
  - Title PR 0 [[PR](http://github.com/repo/PR)] 
  - Title Issue 0 [[Issue](http://github.com/repo/Issue)] 

[`repository-owner-1`](https://github.com/repository-owner-1)
- [`repository-name-1`](https://github.com/repository-owner-1/repository-name-1)
  - Title PR 1 [[PR](http://github.com/repo/PR)] 
  - Title Issue 1 [[Issue](http://github.com/repo/Issue)] 

_PR/Issue review_

[`repository-owner-0`](https://github.com/repository-owner-0)
- [`repository-name-0`](https://github.com/repository-owner-0/repository-name-0)
  - Title Review 0 [[Review](http://github.com/repo/Review)] 

[`repository-owner-1`](https://github.com/repository-owner-1)
- [`repository-name-1`](https://github.com/repository-owner-1/repository-name-1)
  - Title Review 1 [[Review](http://github.com/repo/Review)] 

_Commit summary_

[`repository-owner-0`](https://github.com/repository-owner-0)
- [`repository-name-0`](https://github.com/repository-owner-0/repository-name-0)
  - Title Commit 0 [[Commit](http://github.com/repo/Commit)] 

[`repository-owner-1`](https://github.com/repository-owner-1)
- [`repository-name-1`](https://github.com/repository-owner-1/repository-name-1)
  - Title Commit 1 [[Commit](http://github.com/repo/Commit)] 

_Tags summary_

[`repository-owner-0`](https://github.com/repository-owner-0)
- [`repository-name-0`](https://github.com/repository-owner-0/repository-name-0)
  - Title Tag 0 [[Tag](http://github.com/repo/Tag)] 

[`repository-owner-1`](https://github.com/repository-owner-1)
- [`repository-name-1`](https://github.com/repository-owner-1/repository-name-1)
  - Title Tag 1 [[Tag](http://github.com/repo/Tag)] 
'''

snapshots['test_maybe_write_github_summaries[True] 1'] = '''
_PR/Issue summary_

[\\`repository-owner-0\\`](https://github.com/repository-owner-0)
- [\\`repository-name-0\\`](https://github.com/repository-owner-0/repository-name-0)
  - Title PR 0 [[PR](http://github.com/repo/PR)] 
  - Title Issue 0 [[Issue](http://github.com/repo/Issue)] 

[\\`repository-owner-1\\`](https://github.com/repository-owner-1)
- [\\`repository-name-1\\`](https://github.com/repository-owner-1/repository-name-1)
  - Title PR 1 [[PR](http://github.com/repo/PR)] 
  - Title Issue 1 [[Issue](http://github.com/repo/Issue)] 

_PR/Issue review_

[\\`repository-owner-0\\`](https://github.com/repository-owner-0)
- [\\`repository-name-0\\`](https://github.com/repository-owner-0/repository-name-0)
  - Title Review 0 [[Review](http://github.com/repo/Review)] 

[\\`repository-owner-1\\`](https://github.com/repository-owner-1)
- [\\`repository-name-1\\`](https://github.com/repository-owner-1/repository-name-1)
  - Title Review 1 [[Review](http://github.com/repo/Review)] 

_Commit summary_

[\\`repository-owner-0\\`](https://github.com/repository-owner-0)
- [\\`repository-name-0\\`](https://github.com/repository-owner-0/repository-name-0)
  - Title Commit 0 [[Commit](http://github.com/repo/Commit)] 

[\\`repository-owner-1\\`](https://github.com/repository-owner-1)
- [\\`repository-name-1\\`](https://github.com/repository-owner-1/repository-name-1)
  - Title Commit 1 [[Commit](http://github.com/repo/Commit)] 

_Tags summary_

[\\`repository-owner-0\\`](https://github.com/repository-owner-0)
- [\\`repository-name-0\\`](https://github.com/repository-owner-0/repository-name-0)
  - Title Tag 0 [[Tag](http://github.com/repo/Tag)] 

[\\`repository-owner-1\\`](https://github.com/repository-owner-1)
- [\\`repository-name-1\\`](https://github.com/repository-owner-1/repository-name-1)
  - Title Tag 1 [[Tag](http://github.com/repo/Tag)] 
'''

snapshots['test_maybe_write_misc 1'] = '''
_Misc_

- PR reviews and discussions

Created by https://github.com/benmezger/daily-summary
'''
