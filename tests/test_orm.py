#   Copyright 2013 Matthieu Caneill <matthieu.caneill@gmail.com>
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301
#   USA


import unittest
import glob
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from firehose import orm
from firehose.model import Analysis


class OrmTest(unittest.TestCase):
    def analysis_iterator(self):
        """
        Iterates through the analysises in examples/,
        returns an analysis iterator.
        """
        for filename in sorted(glob.glob('examples/example-*.xml')):
            with open(filename) as f:
                r = Analysis.from_xml(f)
                yield r

    def get_session(self):
        engine = create_engine('sqlite:///:memory:', echo=False)
        orm.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()
        
    def test_orm_values(self):
        """
        Inserts analysises in the db, queries them, and checks that the
        returned values are the same.
        """
        session = self.get_session()
        
        for analysis in self.analysis_iterator():
            session.add(analysis)
            session.commit()
            analysis_back = (session.query(Analysis)
                             .filter(Analysis.id==analysis.id)
                             .first())
            # we check that the returned row is equal to the initial object
            self.assertEqual(analysis, analysis_back)
            

if __name__ == "__main__":
    unittest.main()
