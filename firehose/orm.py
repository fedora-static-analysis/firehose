#   Copyright 2013 David Malcolm <dmalcolm@redhat.com>
#   Copyright 2013 Red Hat, Inc.
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

# partially imported from https://github.com/davidmalcolm/firehose-orm

from sqlalchemy import Table, MetaData, Column,ForeignKey, Integer, \
    String, Float, Index
from sqlalchemy.orm import mapper, relationship, polymorphic_union, \
    sessionmaker, column_property

from firehose.model import Analysis, Result, Issue, Failure, Info, Metadata, \
    Generator, Sut, SourceRpm, DebianBinary, DebianSource, Stats, Message,  \
    Notes, Trace, State, Location, File, Hash, Function, Point, Range, \
    CustomFields


metadata = MetaData()

############################################################################
# Tables
############################################################################

t_analysis = \
    Table('analysis', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('metadata_id', String,
                 ForeignKey('metadata.id'), nullable=False),
          Column('customfields_id', String,
                 ForeignKey('customfields.id')),
          )
Index('ix_analysis_metadata_id', t_analysis.c.metadata_id)

t_generator = \
    Table('generator', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('name', String),
          Column('version', String), # optional in RNG
          )
Index('ix_generator_name_version', t_generator.c.name, t_generator.c.version)

t_metadata = \
    Table('metadata', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('generator_id', String,
                 ForeignKey('generator.id'), nullable=False),
          Column('sut_id', String, ForeignKey('sut.id')),
          Column('file_id', String, ForeignKey('file.id')),
          Column('stats_id', String, ForeignKey('stats.id')),
          )
Index('ix_metadata_generator_id', t_metadata.c.generator_id)
Index('ix_metadata_sut_id', t_metadata.c.sut_id)

t_stats = \
    Table('stats', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('wallclocktime', Float, nullable=False),
          )
Index('ix_metadata_wallclocktime', t_stats.c.wallclocktime)

# For the Sut hierarchy we use joined-table inheritance
t_sut = \
    Table('sut', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('type', String(20), nullable=False),
          Column('name', String, nullable=False),
          Column('version', String, nullable=False),
          Column('release', String),
          Column('buildarch', String),
          )
Index('ix_sut_name_version_release_buildarch',
      t_sut.c.name,
      t_sut.c.version,
      t_sut.c.release,
      t_sut.c.buildarch)

t_result = \
    Table('result', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('type', String(10), nullable=False),
          Column('analysis_id', String,
                 ForeignKey('analysis.id'), nullable=False),
          Column('cwe', Integer),
          Column('testid', String),
          Column('severity', String),
          Column('message_id', String,
                 ForeignKey('message.id')), # not nullable for 'issue' type
          Column('notes_id', String, ForeignKey('notes.id')),
          Column('location_id', String, ForeignKey('location.id')), #  idem
          Column('trace_id', String, ForeignKey('trace.id')),
          Column('customfields_id', String,
                 ForeignKey('customfields.id')),
          )
Index('ix_result_testid', t_result.c.testid)
Index('ix_result_message_id', t_result.c.message_id)
Index('ix_result_location_id', t_result.c.location_id)

t_message = \
    Table('message', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('text', String),
          )
Index('ix_message_text', t_message.c.text)

t_notes = \
    Table('notes', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('text', String),
          )
Index('ix_notes_text', t_notes.c.text)

t_trace = \
    Table('trace', metadata,
          Column('id', String, primary_key=True, autoincrement=False)
          )

t_state = \
    Table('state', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('trace_id', String, ForeignKey('trace.id')),
          Column('location_id', String,
                 ForeignKey('location.id'), nullable=False),
          Column('notes_id', String, ForeignKey('notes.id')),
          )
Index('ix_state_trace_id', t_state.c.trace_id)

t_location = \
    Table('location', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('file_id', String, ForeignKey('file.id'), nullable=False),
          Column('function_id', String, ForeignKey('function.id')),
          # either a point or a range:
          Column('point_id', String, ForeignKey('point.id')),
          Column('range_id', String, ForeignKey('range.id')),
          )
Index('ix_location_file_id_function_id',
      t_location.c.file_id,
      t_location.c.function_id)

t_file = \
    Table('file', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('givenpath', String, nullable=False),
          Column('abspath', String),
          Column('hash_id', String, ForeignKey('hash.id')),
          )
Index('ix_file_givenpath', t_file.c.givenpath)

t_hash = \
    Table('hash', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('alg', String, nullable=False),
          Column('hexdigest', String, nullable=False),
          )
Index('ix_hash_hexdigest', t_hash.c.hexdigest)

t_function = \
    Table('function', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('name', String, nullable=False),
          )
Index('ix_function_name', t_function.c.name)

t_point = \
    Table('point', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('line', Integer, nullable=False),
          Column('column', Integer, nullable=False),
          )
Index('ix_point_line_column', t_point.c.line, t_point.c.column)

t_range = \
    Table('range', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('start_id', String,
                 ForeignKey('point.id'), nullable=False),
          Column('end_id', String,
                 ForeignKey('point.id'), nullable=False),
          )
Index('ix_range_start_id_end_id', t_range.c.start_id, t_range.c.end_id)

t_customfields = \
    Table('customfields', metadata,
          Column('id', String, primary_key=True, autoincrement=False))

t_intfield = \
    Table('intfield', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('customfields_id', String,
                 ForeignKey('customfields.id'), nullable=False),
          Column('name', String, nullable=False),
          Column('value', Integer, nullable=False),
          )
Index('ix_intfield_name', t_intfield.c.name)

t_strfield = \
    Table('strfield', metadata,
          Column('id', String, primary_key=True, autoincrement=False),
          Column('customfields_id', String,
                 ForeignKey('customfields.id'), nullable=False),
          Column('name', String, nullable=False),
          Column('value', String, nullable=False),
          )
Index('ix_strfield_name', t_strfield.c.name)


############################################################################
# Mappers
############################################################################

mapper(Analysis, t_analysis,
       properties={
        'metadata': relationship(Metadata, lazy='joined'),
        'results': relationship(
            Result, order_by=t_result.c.id, lazy='noload'),
        'customfields': relationship(CustomFields),
        }
       )

mapper(Metadata, t_metadata,
       properties={
        'generator': relationship(Generator, lazy='joined'),
        'sut': relationship(Sut, lazy='joined'),
        'file_': relationship(File, lazy='joined'),
        'stats': relationship(Stats, lazy='joined'),
        }
       )

mapper(Generator, t_generator)

# Map the Sut hierarchy using single table inheritance
sut_mapper = mapper(Sut, t_sut,
                    polymorphic_on=t_sut.c.type,
                    polymorphic_identity='sut')

mapper(SourceRpm,
       inherits=sut_mapper,
       polymorphic_identity='source-rpm')

mapper(DebianBinary,
       inherits=sut_mapper,
       polymorphic_identity='debian-binary')

mapper(DebianSource,
       inherits=sut_mapper,
       polymorphic_identity='debian-source')

mapper(Stats, t_stats)
mapper(Message, t_message)
mapper(Notes, t_notes)

mapper(Trace, t_trace,
       properties={
        'states': relationship(
            State, order_by=t_state.c.id, lazy='joined')
        }
       )

mapper(State, t_state,
       properties={
        'location': relationship(Location, lazy='joined'),
        'notes': relationship(Notes, lazy='joined'),
        }
       )

#Map the Result hierarchy using Single Table Inheritance:
result_mapper = mapper(Result, t_result,
       polymorphic_on=t_result.c.type,
       properties={
        'analysis': relationship(Analysis),
        'location': relationship(Location, lazy='joined'),
        'message':  relationship(Message, lazy='joined'),
        'customfields': relationship(CustomFields),
        }
       )

mapper(Issue,
       polymorphic_on=t_result.c.type,
       polymorphic_identity='issue',
       inherits=result_mapper,
       properties={
        'notes':  relationship(Notes, lazy='joined'),
        'trace': relationship(Trace, lazy='joined'),
        }
       )

mapper(Failure,
       inherits=result_mapper,
       polymorphic_on=t_result.c.type,
       polymorphic_identity='failure',
       properties={
        'failureid': t_result.c.testid, # we use the testid field
        }
       )

mapper(Info,
       inherits=result_mapper,
       polymorphic_identity='info',
       properties={
        'infoid': t_result.c.testid, # we use the testid field
        }
       )

mapper(Location, t_location,
       properties={
        'file': relationship(File, lazy='joined'),
        'function': relationship(Function, lazy='joined'),
        'point': relationship(Point, lazy='joined'),
        'range_': relationship(Range, lazy='joined'),
        }
       )

mapper(File, t_file,
       properties={
        'hash_': relationship(Hash, lazy='joined'),
        }
       )

mapper(Hash, t_hash)

mapper(Function, t_function)

mapper(Point, t_point)

mapper(Range, t_range,
       properties={
        'start': relationship(Point, foreign_keys=t_range.c.start_id,
                              lazy='joined'),
        'end': relationship(Point, foreign_keys=t_range.c.end_id,
                            lazy='joined')
        # foreign_keys specified to avoid ambiguity
        }
       )

mapper(CustomFields, t_customfields)
