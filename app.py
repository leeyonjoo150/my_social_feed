import streamlit as st
from auth import show_auth_page, logout_user
from user_manager import UserManager
from post_manager import PostManager

#화면구성 단계
# 페이지 설정
st.set_page_config(
    page_title="peach's post",
    page_icon="🍑",
    layout="wide"
)

# 메뉴 옵션 상수 정의
#에러 후 수정
MENU_OPTIONS = ["🏠 홈", "✍️ 포스트 작성", "📋 내 포스트", "👤 프로필"]

def show_home_page(current_user, post_mgr, user_mgr):
    """홈 화면 - 실제 게시글 목록"""
    st.header("📝 최근 포스트")

    # 작성자 검색 기능 추가
    search_col1, search_col2, search_col3 = st.columns([6, 1, 1])
    
    with search_col1:
        search_author = st.text_input("🔍 작성자 검색", placeholder="작성자명을 입력하세요...", key="search_author_input")
    
    with search_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # HTML 줄바꿈으로 더 정확한 높이 조정
        if st.button("🔍 검색", use_container_width=True):
            if search_author.strip():
                st.session_state.search_filter = search_author.strip()
            else:
                st.session_state.search_filter = ""
    
    with search_col3:
        st.markdown("<br>", unsafe_allow_html=True)  # HTML 줄바꿈으로 더 정확한 높이 조정
        if st.button("⬅️ 전체보기", use_container_width=True):
            st.session_state.search_filter = ""
            st.rerun()

    # 검색 필터 상태 초기화
    if 'search_filter' not in st.session_state:
        st.session_state.search_filter = ""

    # 게시글 불러오기
    posts_with_stats = post_mgr.get_posts_with_stats()

    if len(posts_with_stats) == 0:
        st.info("📝 아직 작성된 포스트가 없습니다. 첫 번째 포스트를 작성해보세요!")
        if st.button("✍️ 포스트 작성하러 가기"):
            st.session_state.menu = "✍️ 포스트 작성"
            st.rerun()
        return

    # 사용자 이름 가져오기 위해 users와 조인
    users_df = user_mgr.load_users()
    posts_display = posts_with_stats.merge(
        users_df[['user_id', 'username']],
        on='user_id',
        how='left'
    )

    # 작성자 검색 필터 적용
    if st.session_state.search_filter:
        search_term = st.session_state.search_filter.lower()
        filtered_posts = posts_display[
            posts_display['username'].str.lower().str.contains(search_term, na=False)
        ]
        
        # 검색 결과 표시
        if len(filtered_posts) > 0:
            st.success(f"🔍 '{st.session_state.search_filter}' 검색 결과: {len(filtered_posts)}개의 포스트를 찾았습니다.")
            posts_display = filtered_posts
        else:
            st.warning(f"🔍 '{st.session_state.search_filter}' 작성자의 포스트를 찾을 수 없습니다.")
            posts_display = pd.DataFrame()  # 빈 데이터프레임
    
    # 검색 결과가 있거나 검색하지 않은 경우 포스트 표시
    if len(posts_display) > 0:
    # 게시글 하나씩 표시
        for idx, post in posts_display.iterrows():
            with st.container():
                # 프로필 이미지와 정보
                col1, col2 = st.columns([1, 11])

                with col1:
                    st.image("https://images.unsplash.com/photo-1743449661678-c22cd73b338a?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHwzfHx8ZW58MHx8fHx8", width=50)

                with col2:
                    # 사용자 정보와 액션 버튼
                    col_info, col_action = st.columns([8, 4])

                    with col_info:
                        time_str = post['timestamp'].split(' ')[1][:5]  # HH:MM 형식
                        st.markdown(f"**{post['username']}** • {time_str}")

                    with col_action:
                        # 삭제 버튼 (작성자만)
                        if post['user_id'] == current_user['user_id']:
                            if st.button("🗑️", key=f"del_{post['post_id']}", help="삭제"):
                                if post_mgr.delete_post(post['post_id'], current_user['user_id']):
                                    st.success("게시글이 삭제되었습니다!")
                                    st.rerun()

                    # 게시글 내용
                    st.markdown(post['content'])

                    # 좋아요, 리트윗 버튼 (새로운 레이아웃)
                    col_like, col_retweet, col_space = st.columns([2, 2, 8])

                    with col_like : 
                        is_liked = post_mgr.is_liked_by_user(current_user['user_id'], post['post_id'])
                        like_emoji = "❤️" if is_liked else "🤍"
                        like_count = int(post['like_count'])

                        if st.button(f"{like_emoji} {like_count}", key=f"like_{post['post_id']}"):
                            liked = post_mgr.toggle_like(current_user['user_id'], post['post_id'])
                            if liked:
                                st.success("좋아요!")
                            else:
                                st.info("좋아요 취소")
                            st.rerun()

                    with col_retweet:  # 새로 추가
                        is_retweeted = post_mgr.is_retweeted_by_user(current_user['user_id'], post['post_id'])
                        retweet_emoji = "🔄" if is_retweeted else "↻"
                        retweet_count = int(post['retweet_count'])
                        
                        if st.button(f"{retweet_emoji} {retweet_count}", key=f"retweet_{post['post_id']}"):
                            retweeted = post_mgr.toggle_retweet(current_user['user_id'], post['post_id'])
                            if retweeted:
                                st.success("리트윗!")
                            else:
                                st.info("리트윗 취소")
                            st.rerun()

            st.divider()

def show_write_page(current_user, post_mgr):
    """글쓰기 페이지"""
    st.header("✍️ 새 포스트 작성")

    st.markdown("💡 **다른 사람들에게 공유하고 싶은 포스트를 작성해보세요**")

    # 글쓰기 폼
    with st.form("write_form", clear_on_submit=True):
        content = st.text_area(
            "포스트 내용",
            placeholder="포스트 내용을 작성해주세요",
            height=200
        )

        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            submitted = st.form_submit_button("🚀 게시하기", type="primary")

        if submitted:
            if content.strip():
                success = post_mgr.create_post(current_user['user_id'], content.strip())

                if success:
                    st.success("포스트가 게시되었습니다! 🎉")
                    st.balloons()
                    import time
                    time.sleep(1.5)  # 1.5초 잠시 멈춤
                    st.session_state.menu = "🏠 홈"
                    st.rerun()
                else:
                    st.error("게시 중 오류가 발생했습니다.")
            else:
                st.error("내용을 입력해주세요!")

    st.divider()

def show_profile_page(current_user, post_mgr, user_mgr):
    """프로필 페이지 - 간단 버전"""
    st.header("👤 내 프로필")

    # 기본 정보
    col1, col2 = st.columns([1, 3])

    with col1:
        st.image("https://images.unsplash.com/photo-1743449661678-c22cd73b338a?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHwzfHx8ZW58MHx8fHx8", width=100)

    with col2:
        st.markdown(f"### {current_user['username']}")
        st.markdown(f"**가입일:** {current_user['created_at']}")

    st.divider()

    # 내가 쓴 글 목록
    st.subheader("📝 내가 작성한 포스트")

    posts_with_stats = post_mgr.get_posts_with_stats()

    # DataFrame이 비어있거나 user_id 컬럼이 없는 경우 체크
    if len(posts_with_stats) == 0 or 'user_id' not in posts_with_stats.columns:
        st.info("📝 아직 작성한 포스트가 없습니다.")
        if st.button("✍️ 첫 포스트 작성하기"):
            st.session_state.menu = "✍️ 포스트 작성"
            st.rerun()
        return

    my_posts = posts_with_stats[posts_with_stats['user_id'] == current_user['user_id']]

    if len(my_posts) > 0:
        st.info(f"총 {len(my_posts)}개의 포스트를 작성했습니다.")

        for idx, post in my_posts.iterrows():
            with st.container():
                col1, col2 = st.columns([8, 4])

                with col1:
                    # 내용 미리보기 (100자)
                    preview = post['content'][:100] + "..." if len(post['content']) > 100 else post['content']
                    st.markdown(f"**{preview}**")
                    st.caption(f"작성: {post['timestamp']} • 좋아요: {int(post['like_count'])}개 • 리트윗: {int(post['retweet_count'])}개")

                with col2:
                    if st.button("🗑️ 삭제", key=f"profile_del_{post['post_id']}"):
                        if post_mgr.delete_post(post['post_id'], current_user['user_id']):
                            st.success("삭제되었습니다!")
                            st.rerun()

            st.divider()
    else:
        st.info("📝 아직 작성한 포스트가 없습니다.")
        if st.button("✍️ 첫 포스트 작성하기"):
            st.session_state.menu = "✍️ 포스트 작성"
            st.rerun()

def show_my_posts_page(current_user, post_mgr, user_mgr):
    """내 포스트 페이지 - 내가 쓴 글, 리트윗한 글, 좋아요 누른 글"""
    st.header("📋 내 포스트")

    tab1, tab2, tab3 = st.tabs(["✍️ 내가 쓴 글", "🔄 리트윗한 글", "❤️ 좋아요 누른 글"])

    # 모든 포스트 데이터 불러오기
    posts_with_stats = post_mgr.get_posts_with_stats()
    users_df = user_mgr.load_users()
    
    # 데이터가 있는지 확인
    if len(posts_with_stats) == 0:
        with tab1:
            st.info("📝 아직 작성된 포스트가 없습니다.")
        with tab2:
            st.info("🔄 아직 리트윗한 포스트가 없습니다.")
        with tab3:
            st.info("❤️ 아직 좋아요를 누른 포스트가 없습니다.")
        return

    # 사용자 이름과 조인
    posts_display = posts_with_stats.merge(
        users_df[['user_id', 'username']],
        on='user_id',
        how='left'
    )

    # 탭 1: 내가 쓴 글
    with tab1:
        my_posts = posts_display[posts_display['user_id'] == current_user['user_id']]
        
        if len(my_posts) > 0:
            st.info(f"총 {len(my_posts)}개의 포스트를 작성했습니다.")
            
            for idx, post in my_posts.iterrows():
                display_post_card(post, current_user, post_mgr, show_delete=True, key_prefix="my")
        else:
            st.info("📝 아직 작성한 포스트가 없습니다.")
            if st.button("✍️ 첫 포스트 작성하기", key="write_first_post"):
                st.session_state.menu = "✍️ 포스트 작성"
                st.rerun()

    # 탭 2: 리트윗한 글
    with tab2:
        retweet_df = post_mgr.load_retweet()
        my_retweets = retweet_df[retweet_df['user_id'] == current_user['user_id']]
        
        if len(my_retweets) > 0:
            # 내가 리트윗한 포스트들 가져오기
            retweeted_post_ids = my_retweets['post_id'].tolist()
            retweeted_posts = posts_display[posts_display['post_id'].isin(retweeted_post_ids)]
            
            st.info(f"총 {len(retweeted_posts)}개의 포스트를 리트윗했습니다.")
            
            for idx, post in retweeted_posts.iterrows():
                # 리트윗 표시 추가
                st.markdown("🔄 **리트윗했습니다**")
                display_post_card(post, current_user, post_mgr, show_delete=False, key_prefix="retweet")
        else:
            st.info("🔄 아직 리트윗한 포스트가 없습니다.")

    # 탭 3: 좋아요 누른 글
    with tab3:
        likes_df = post_mgr.load_likes()
        my_likes = likes_df[likes_df['user_id'] == current_user['user_id']]
        
        if len(my_likes) > 0:
            # 내가 좋아요한 포스트들 가져오기
            liked_post_ids = my_likes['post_id'].tolist()
            liked_posts = posts_display[posts_display['post_id'].isin(liked_post_ids)]
            
            st.info(f"총 {len(liked_posts)}개의 포스트에 좋아요를 눌렀습니다.")
            
            for idx, post in liked_posts.iterrows():
                # 좋아요 표시 추가
                st.markdown("❤️ **좋아요를 눌렀습니다**")
                display_post_card(post, current_user, post_mgr, show_delete=False, key_prefix="liked")
        else:
            st.info("❤️ 아직 좋아요를 누른 포스트가 없습니다.")

def display_post_card(post, current_user, post_mgr, show_delete=False, key_prefix=""):
    """포스트 카드 표시 함수 (재사용 가능)"""
    with st.container():
        # 프로필 이미지와 정보
        col1, col2 = st.columns([1, 11])

        with col1:
            st.image("https://images.unsplash.com/photo-1743449661678-c22cd73b338a?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHwzfHx8ZW58MHx8fHx8", width=50)

        with col2:
            # 사용자 정보와 액션 버튼
            if show_delete:
                col_info, col_action = st.columns([8, 4])
                
                with col_action:
                    if st.button("🗑️ 삭제", key=f"{key_prefix}_del_{post['post_id']}", help="삭제"):
                        if post_mgr.delete_post(post['post_id'], current_user['user_id']):
                            st.success("게시글이 삭제되었습니다!")
                            st.rerun()
            else:
                col_info = st.columns([1])[0]

            with col_info:
                time_str = post['timestamp'].split(' ')[1][:5]  # HH:MM 형식
                st.markdown(f"**{post['username']}** • {time_str}")

            # 게시글 내용
            st.markdown(post['content'])

            # 좋아요, 리트윗 버튼
            col_like, col_retweet, col_space = st.columns([2, 2, 8])

            with col_like:
                is_liked = post_mgr.is_liked_by_user(current_user['user_id'], post['post_id'])
                like_emoji = "❤️" if is_liked else "🤍"
                like_count = int(post['like_count'])

                if st.button(f"{like_emoji} {like_count}", key=f"{key_prefix}_like_{post['post_id']}"):
                    liked = post_mgr.toggle_like(current_user['user_id'], post['post_id'])
                    if liked:
                        st.success("좋아요!")
                    else:
                        st.info("좋아요 취소")
                    st.rerun()

            with col_retweet:
                is_retweeted = post_mgr.is_retweeted_by_user(current_user['user_id'], post['post_id'])
                retweet_emoji = "🔄" if is_retweeted else "↻"
                retweet_count = int(post['retweet_count'])
                
                if st.button(f"{retweet_emoji} {retweet_count}", key=f"{key_prefix}_retweet_{post['post_id']}"):
                    retweeted = post_mgr.toggle_retweet(current_user['user_id'], post['post_id'])
                    if retweeted:
                        st.success("리트윗!")
                    else:
                        st.info("리트윗 취소")
                    st.rerun()

    st.divider()

# 매니저 초기화
@st.cache_resource
def init_managers():
    return UserManager(), PostManager()

user_mgr, post_mgr = init_managers()

# Session State 초기화 (새 접속시 자동 로그아웃)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'menu' not in st.session_state or st.session_state.menu not in MENU_OPTIONS :
    # 원래 작성 코드
    # st.session_state.menu = "🏠 홈"
    #에러 후 수정 코드
    st.session_state.menu = MENU_OPTIONS[0]

# 로그인 체크
if not st.session_state.logged_in:
    # 로그인하지 않은 경우
    show_auth_page()

else:
    # 로그인한 경우 - 메인 앱
    current_user = st.session_state.current_user

    # 헤더 영역
    col1, col2 = st.columns([4, 1])
    with col1 :
        st.title("🍑 소셜 피드")
        st.markdown(f"**{current_user['username']}님 환영합니다!**")
    with col2 :
        if st.button("🚪 로그아웃") :
            logout_user()
            
    # 사이드바 - 네비게이션
    st.sidebar.title("📋 메뉴")
    st.sidebar.markdown(f"👤 **{current_user['username']}**")
    #st.sidebar.markdown(f"🆔 {current_user['user_id']}")
    #수정 전, 에러 전
    # menu = st.sidebar.selectbox(
    #     "📋 메뉴",
    #     ["🏠 홈", "✍️ 포스트 작성", "📋 내 포스트", "👤 프로필"].index(st.session_state.menu)
    # )
    try:
        current_index = MENU_OPTIONS.index(st.session_state.menu)
    except ValueError:
        current_index = 0
        st.session_state.menu = MENU_OPTIONS[0]
    
    menu = st.sidebar.selectbox(
        "📋 메뉴",
        MENU_OPTIONS,
        index=current_index
    )

    # 메뉴 변경 감지
    if menu != st.session_state.menu:
        st.session_state.menu = menu
        st.rerun()

    # 메인 영역
    if menu == "🏠 홈":
        show_home_page(current_user, post_mgr, user_mgr)

    elif menu == "✍️ 포스트 작성":
        show_write_page(current_user, post_mgr)

    elif menu == "👤 프로필":
        show_profile_page(current_user, post_mgr, user_mgr)

    elif menu == "📋 내 포스트" :
        show_my_posts_page(current_user, post_mgr, user_mgr)