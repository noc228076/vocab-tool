"""Add missing phonetic transcriptions for CET-4/6 words"""
import json
from pathlib import Path

PHONETICS = {
    'lately': '/ˈleɪtli/',
    'tour': '/tʊr/',
    'degree': '/dɪˈɡriː/',
    'professor': '/prəˈfesər/',
    'pale': '/peɪl/',
    'aural': '/ˈɔːrəl/',
    'really': '/ˈriːəli/',
    'suspicion': '/səˈspɪʃn/',
    'orchestra': '/ˈɔːrkɪstrə/',
    'probably': '/ˈprɑːbəbli/',
    'nonsense': '/ˈnɑːnsens/',
    'resident': '/ˈrezɪdənt/',
    'systematic': '/ˌsɪstəˈmætɪk/',
    'divorce': '/dɪˈvɔːrs/',
    'occasionally': '/əˈkeɪʒnəli/',
    'border': '/ˈbɔːrdər/',
    'attack': '/əˈtæk/',
    'paw': '/pɔː/',
    'injury': '/ˈɪndʒəri/',
    'detection': '/dɪˈtekʃn/',
    'chemical': '/ˈkemɪkl/',
    'expression': '/ɪkˈspreʃn/',
    'generation': '/ˌdʒenəˈreɪʃn/',
    'implication': '/ˌɪmplɪˈkeɪʃn/',
    'kind': '/kaɪnd/',
    'universe': '/ˈjuːnɪvɜːrs/',
    'conversely': '/ˈkɑːnvɜːrsli/',
    'differentiate': '/ˌdɪfəˈrenʃieɪt/',
    'upwards': '/ˈʌpwərdz/',
    'distort': '/dɪˈstɔːrt/',
    'specification': '/ˌspesɪfɪˈkeɪʃn/',
    'ignorance': '/ˈɪɡnərəns/',
    'questionnaire': '/ˌkwestʃəˈner/',
    'faulty': '/ˈfɔːlti/',
    'congress': '/ˈkɑːŋɡrəs/',
    'redundant': '/rɪˈdʌndənt/',
    'commentator': '/ˈkɑːmənteɪtər/',
    'verse': '/vɜːrs/',
    'fossil': '/ˈfɑːsl/',
    'democracy': '/dɪˈmɑːkrəsi/',
    'parachute': '/ˈpærəʃuːt/',
    'confrontation': '/ˌkɑːnfrənˈteɪʃn/',
    'nursery': '/ˈnɜːrsəri/',
    'subjective': '/səbˈdʒektɪv/',
    'productivity': '/ˌprɑːdʌkˈtɪvəti/',
    'propaganda': '/ˌprɑːpəˈɡændə/',
    'setup': '/ˈsetʌp/',
    'classification': '/ˌklæsɪfɪˈkeɪʃn/',
    'defective': '/dɪˈfektɪv/',
    'commentary': '/ˈkɑːmənteri/',
    'treaty': '/ˈtriːti/',
    'conscientious': '/ˌkɑːnʃiˈenʃəs/',
    'dioxide': '/daɪˈɑːksaɪd/',
    'colonist': '/ˈkɑːlənɪst/',
    'competence': '/ˈkɑːmpɪtəns/',
    'deflect': '/dɪˈflekt/',
    'guardian': '/ˈɡɑːrdiən/',
    'monastery': '/ˈmɑːnəsteri/',
    'terminology': '/ˌtɜːrmɪˈnɑːlədʒi/',
    'artery': '/ˈɑːrtəri/',
    'vanguard': '/ˈvænɡɑːrd/',
    'allot': '/əˈlɑːt/',
    'infantry': '/ˈɪnfəntri/',
    'predecessor': '/ˈpredəsesər/',
    'autobiography': '/ˌɔːtəbaɪˈɑːɡrəfi/',
    'nobility': '/noʊˈbɪləti/',
    'caravan': '/ˈkærəvæn/',
    'mountainous': '/ˈmaʊntɪnəs/',
    'detach': '/dɪˈtætʃ/',
    'carbohydrate': '/ˌkɑːrboʊˈhaɪdreɪt/',
    'constraint': '/kənˈstreɪnt/',
    'petty': '/ˈpeti/',
    'magistrate': '/ˈmædʒɪstreɪt/',
    'nickel': '/ˈnɪkl/',
    'tropic': '/ˈtrɑːpɪk/',
    'liner': '/ˈlaɪnər/',
    'clerical': '/ˈklerɪkl/',
    'newscaster': '/ˈnuːzkæstər/',
    'excerpt': '/ˈeksɜːrpt/',
    'fore': '/fɔːr/',
    'shipyard': '/ˈʃɪpjɑːrd/',
    'howl': '/haʊl/',
    'denote': '/dɪˈnoʊt/',
    'habitation': '/ˌhæbɪˈteɪʃn/',
    'hegemony': '/hɪˈdʒeməni/',
    'sediment': '/ˈsedɪmənt/',
    'dissent': '/dɪˈsent/',
    'wig': '/wɪɡ/',
    'ragged': '/ˈræɡɪd/',
    'slum': '/slʌm/',
    'detergent': '/dɪˈtɜːrdʒənt/',
    'stellar': '/ˈstelər/',
    'ammonia': '/əˈmoʊniə/',
    'yacht': '/jɑːt/',
    'clamour': '/ˈklæmər/',

    # second batch - CET-4
    'import': '/ɪmˈpɔːrt/',
    'intend': '/ɪnˈtend/',
    'direction': '/dəˈrekʃn/',
    'deepen': '/ˈdiːpən/',
    'shed': '/ʃed/',
    'reservoir': '/ˈrezərvwɑːr/',
    'official': '/əˈfɪʃl/',
    'drama': '/ˈdrɑːmə/',
    'desk': '/desk/',
    'overhead': '/ˌoʊvərˈhed/',
    'serve': '/sɜːrv/',
    'silver': '/ˈsɪlvər/',
    'from': '/frʌm/',
    'simplicity': '/sɪmˈplɪsəti/',
    'provided': '/prəˈvaɪdɪd/',
    'device': '/dɪˈvaɪs/',
    'loan': '/loʊn/',
    'furniture': '/ˈfɜːrnɪtʃər/',
    'ocean': '/ˈoʊʃn/',
    'justify': '/ˈdʒʌstɪfaɪ/',
    'cigaret': '/ˌsɪɡəˈret/',
    'bitter': '/ˈbɪtər/',
    'needless': '/ˈniːdləs/',
    'specific': '/spəˈsɪfɪk/',
    'layout': '/ˈleɪaʊt/',
    'impatient': '/ɪmˈpeɪʃnt/',
    'ampere': '/ˈæmpɪr/',
    'penetrate': '/ˈpenətreɪt/',
    'disorder': '/dɪsˈɔːrdər/',
    'anybody': '/ˈenibʌdi/',
    'bark': '/bɑːrk/',
    'recovery': '/rɪˈkʌvəri/',
    'brittle': '/ˈbrɪtl/',
    'guarantee': '/ˌɡærənˈtiː/',
    'extent': '/ɪkˈstent/',
    'mercury': '/ˈmɜːrkjəri/',
    'ray': '/reɪ/',
    'melt': '/melt/',
    # CET-6
    'resultant': '/rɪˈzʌltənt/',
    'watchful': '/ˈwɑːtʃfl/',
    'brace': '/breɪs/',
    'symptom': '/ˈsɪmptəm/',
    'finite': '/ˈfaɪnaɪt/',
    'commonsense': '/ˌkɑːmənˈsens/',

    'psychology': '/saɪˈkɑːlədʒi/',
    'mingle': '/ˈmɪŋɡl/',
    'experimentally': '/ɪkˌsperɪˈmentəli/',
    'scarcity': '/ˈskersəti/',
    'siren': '/ˈsaɪrən/',
    'reptile': '/ˈreptaɪl/',

    'sensitivity': '/ˌsensəˈtɪvəti/',
    'charm': '/tʃɑːrm/',
    'courtesy': '/ˈkɜːrtəsi/',
    'guitar': '/ɡɪˈtɑːr/',
    'radical': '/ˈrædɪkl/',
    'ingenuity': '/ˌɪndʒəˈnuːəti/',
    'workpiece': '/ˈwɜːrkpiːs/',

    'valve': '/vælv/',
    'fighter': '/ˈfaɪtər/',
    'summit': '/ˈsʌmɪt/',
    'mortgage': '/ˈmɔːrɡɪdʒ/',
    'errand': '/ˈerənd/',
    'ascertain': '/ˌæsərˈteɪn/',
    'manifest': '/ˈmænɪfest/',
    'baseball': '/ˈbeɪsbɔːl/',
    'eclipse': '/ɪˈklɪps/',
    'pedlar': '/ˈpedlər/',
    'xerox': '/ˈzɪrɑːks/',
    # capitalized
    'mister': '/ˈmɪstər/',
    'islam': '/ˈɪzlɑːm/',
    'saturn': '/ˈsætɜːrn/',
    'thanksgiving': '/ˌθæŋksˈɡɪvɪŋ/',
}

def main():
    words_file = Path(__file__).parent.parent / "data" / "words.json"
    with open(words_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixed = 0
    for cat in ('cet4', 'cet6', 'custom'):
        for w in data.get(cat, []):
            word = w['word']
            ph = w.get('phonetic', '').strip()
            if ph:
                continue
            wrd_key = word.lower()
            if wrd_key in PHONETICS:
                w['phonetic'] = PHONETICS[wrd_key]
                fixed += 1
            elif word in PHONETICS:
                w['phonetic'] = PHONETICS[word]
                fixed += 1
    
    with open(words_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    Path('tmp_fixed_count.txt').write_text(str(fixed), encoding='utf-8')

if __name__ == '__main__':
    main()
