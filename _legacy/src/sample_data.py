"""Sample curriculum data so the demo works immediately without uploads."""

from src.models import Topic
from src.database import save_topics, save_profile
from src.models import UserProfile
from datetime import date, timedelta
import uuid


def create_sample_curriculum():
    """Create a realistic sample syllabus for Computer Science / Engineering students."""
    topics = [
        # Operating Systems
        Topic(id=str(uuid.uuid4()), subject="Operating Systems", title="Process Management & Scheduling",
              description="CPU scheduling algorithms, process states, context switching",
              weightage=4.0, difficulty=2.5, estimated_minutes=35, mastery=15.0),
        Topic(id=str(uuid.uuid4()), subject="Operating Systems", title="Memory Management & Paging",
              description="Virtual memory, page replacement, segmentation",
              weightage=4.5, difficulty=3.0, estimated_minutes=40, mastery=10.0),
        Topic(id=str(uuid.uuid4()), subject="Operating Systems", title="Deadlocks",
              description="Necessary conditions, prevention, avoidance, detection",
              weightage=3.5, difficulty=2.8, estimated_minutes=30, mastery=25.0),
        Topic(id=str(uuid.uuid4()), subject="Operating Systems", title="File Systems",
              description="File allocation methods, directory structure, free space management",
              weightage=3.0, difficulty=2.0, estimated_minutes=25, mastery=40.0),

        # DBMS
        Topic(id=str(uuid.uuid4()), subject="Database Systems", title="ER Model & Relational Model",
              description="Entity-relationship diagrams, keys, integrity constraints",
              weightage=3.5, difficulty=2.0, estimated_minutes=30, mastery=55.0),
        Topic(id=str(uuid.uuid4()), subject="Database Systems", title="SQL Queries & Joins",
              description="Complex selects, joins, subqueries, aggregation",
              weightage=4.5, difficulty=2.5, estimated_minutes=35, mastery=35.0),
        Topic(id=str(uuid.uuid4()), subject="Database Systems", title="Normalization (1NF to 5NF)",
              description="Functional dependencies, normal forms, decomposition",
              weightage=4.0, difficulty=3.2, estimated_minutes=40, mastery=20.0),
        Topic(id=str(uuid.uuid4()), subject="Database Systems", title="Transactions & Concurrency",
              description="ACID properties, schedules, locking, isolation levels",
              weightage=4.0, difficulty=3.0, estimated_minutes=35, mastery=12.0),

        # Computer Networks
        Topic(id=str(uuid.uuid4()), subject="Computer Networks", title="OSI & TCP/IP Models",
              description="Layered architecture, responsibilities of each layer",
              weightage=3.5, difficulty=2.0, estimated_minutes=25, mastery=60.0),
        Topic(id=str(uuid.uuid4()), subject="Computer Networks", title="IP Addressing & Subnetting",
              description="IPv4, CIDR, subnet masks, network design",
              weightage=4.0, difficulty=2.8, estimated_minutes=35, mastery=30.0),
        Topic(id=str(uuid.uuid4()), subject="Computer Networks", title="Routing Algorithms",
              description="Distance vector, link state, BGP basics",
              weightage=3.5, difficulty=3.0, estimated_minutes=30, mastery=18.0),
        Topic(id=str(uuid.uuid4()), subject="Computer Networks", title="Transport Layer (TCP/UDP)",
              description="Reliable delivery, flow control, congestion control",
              weightage=4.0, difficulty=2.7, estimated_minutes=30, mastery=22.0),

        # DSA / Algorithms
        Topic(id=str(uuid.uuid4()), subject="Algorithms", title="Time & Space Complexity",
              description="Big-O, best/average/worst case, analyzing code",
              weightage=4.5, difficulty=2.5, estimated_minutes=30, mastery=45.0),
        Topic(id=str(uuid.uuid4()), subject="Algorithms", title="Sorting Algorithms",
              description="Quick, Merge, Heap, Counting – comparisons and use cases",
              weightage=3.5, difficulty=2.3, estimated_minutes=30, mastery=50.0),
        Topic(id=str(uuid.uuid4()), subject="Algorithms", title="Graph Algorithms (BFS/DFS)",
              description="Traversal, shortest path basics, applications",
              weightage=4.0, difficulty=3.0, estimated_minutes=40, mastery=28.0),
        Topic(id=str(uuid.uuid4()), subject="Algorithms", title="Dynamic Programming Basics",
              description="Memoization, tabulation, classic problems",
              weightage=4.5, difficulty=3.5, estimated_minutes=45, mastery=8.0),
    ]

    save_topics(topics)

    # Default profile
    profile = UserProfile(
        name="Alex",
        exam_date=date.today() + timedelta(days=18),
        daily_available_hours=3.5,
        subjects=["Operating Systems", "Database Systems", "Computer Networks", "Algorithms"]
    )
    save_profile(profile)

    return topics, profile


def get_or_create_sample():
    from src.database import load_topics, load_profile
    topics = load_topics()
    profile = load_profile()
    if not topics or not profile:
        return create_sample_curriculum()
    return topics, profile